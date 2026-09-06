"""Cross-session SkillProfile aggregation (Phase 6b).

recompute_for_user() rebuilds a candidate's whole SkillProfile from scratch
from their completed InterviewSessions every time it's called, rather than
maintaining incremental running-mean state. That makes it idempotent (safe
to call twice), self-correcting (no drift from incremental-average bugs),
and simple to test with direct data-layer fixtures. At realistic scale
(tens of sessions, single/low-double-digit turns each) this is a cheap
Postgres read + Python aggregation - no LLM/embedding call at all, so
unlike resume parsing this stays inline in the request that completes a
session (see interview_session_service.submit_answer()) rather than going
through the async task queue.

Topics are grouped by simple case/whitespace normalization only (topic_key).
There is no taxonomy that maps differently-phrased-but-same-skill topic
strings together - see docs/architecture.md's Phase 6b note for why that's
a deliberate, documented limitation rather than an oversight.
"""

import uuid
from statistics import mean

from sqlalchemy.orm import Session as DBSession, selectinload

from app.core.config import settings
from app.models import InterviewSession, InterviewTurn, SkillProfile, SkillProfileTopicStat
from app.repositories import skill_profile_repository


def _classify_trend(last_session_score: float, previous_session_score: float | None) -> str:
    if previous_session_score is None:
        return "insufficient_data"
    delta = last_session_score - previous_session_score
    if delta > settings.skill_trend_delta_threshold:
        return "improving"
    if delta < -settings.skill_trend_delta_threshold:
        return "declining"
    return "stable"


def _combined_score(turn: InterviewTurn) -> float:
    return (turn.technical_score + turn.communication_score + turn.completeness_score) / 3


def recompute_for_user(db: DBSession, user_id: uuid.UUID) -> SkillProfile:
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id, InterviewSession.status == "complete")
        .options(selectinload(InterviewSession.turns))
        .order_by(InterviewSession.completed_at)
        .all()
    )

    overall_technical: list[float] = []
    overall_communication: list[float] = []
    overall_completeness: list[float] = []
    # topic_key -> {"label": str, "turns": [InterviewTurn], "session_scores": [float, ...]}
    topics: dict[str, dict] = {}

    for session in sessions:
        scored_turns = [
            t for t in session.turns if None not in (t.technical_score, t.communication_score, t.completeness_score)
        ]
        session_topic_turns: dict[str, list[InterviewTurn]] = {}
        for turn in scored_turns:
            overall_technical.append(turn.technical_score)
            overall_communication.append(turn.communication_score)
            overall_completeness.append(turn.completeness_score)

            topic_key = turn.topic.strip().lower()
            entry = topics.setdefault(topic_key, {"label": turn.topic, "turns": [], "session_scores": []})
            entry["label"] = turn.topic
            entry["turns"].append(turn)
            session_topic_turns.setdefault(topic_key, []).append(turn)

        for topic_key, turns in session_topic_turns.items():
            topics[topic_key]["session_scores"].append(mean(_combined_score(t) for t in turns))

    profile = skill_profile_repository.get_or_create(db, user_id)
    skill_profile_repository.update_aggregate(
        db,
        profile,
        sessions_completed=len(sessions),
        overall_avg_technical_score=mean(overall_technical) if overall_technical else None,
        overall_avg_communication_score=mean(overall_communication) if overall_communication else None,
        overall_avg_completeness_score=mean(overall_completeness) if overall_completeness else None,
    )

    topic_stats = []
    for topic_key, data in topics.items():
        turns = data["turns"]
        session_scores = data["session_scores"]
        last_session_score = session_scores[-1]
        previous_session_score = session_scores[-2] if len(session_scores) >= 2 else None
        topic_stats.append(
            SkillProfileTopicStat(
                topic_key=topic_key,
                topic_label=data["label"],
                sessions_count=len(session_scores),
                turns_count=len(turns),
                avg_technical_score=mean(t.technical_score for t in turns),
                avg_communication_score=mean(t.communication_score for t in turns),
                avg_completeness_score=mean(t.completeness_score for t in turns),
                last_session_score=last_session_score,
                previous_session_score=previous_session_score,
                trend=_classify_trend(last_session_score, previous_session_score),
            )
        )
    skill_profile_repository.replace_topic_stats(db, profile, topic_stats)

    return profile
