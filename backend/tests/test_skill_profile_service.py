"""SkillProfile aggregation tests.

Sessions are seeded directly at the data layer (TestSessionLocal +
interview_session_repository + raw InterviewTurn rows), not driven through
a full multi-turn API/LLM interview flow - mirrors Phase 4b's pattern of
seeding state directly via repositories (see test_interview_session_state.py)
rather than always going through the full stack. This makes "session 1
completed, then session 2 completed" cheap and deterministic to set up.
"""

import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import decode_access_token
from app.models import InterviewTurn
from app.repositories import interview_session_repository, skill_profile_repository
from app.services import skill_profile_service
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_sessions import _ready_plan

_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _seed_completed_session(user_id: uuid.UUID, plan_id: str, turns: list[tuple[str, float, float, float]], *, completed_at: datetime) -> uuid.UUID:
    """turns: list of (topic, technical_score, communication_score, completeness_score)."""
    db = TestSessionLocal()
    try:
        session = interview_session_repository.create(
            db,
            user_id=user_id,
            interview_plan_id=uuid.UUID(plan_id),
            total_questions=len(turns),
            current_difficulty=3,
            topic_queue=[],
            asked_questions=[],
            cost_cap_usd=2.0,
        )
        for idx, (topic, technical, communication, completeness) in enumerate(turns):
            db.add(
                InterviewTurn(
                    session_id=session.id,
                    idx=idx,
                    topic=topic,
                    difficulty=3,
                    question_text=f"Question {idx}",
                    answer_text="an answer",
                    technical_score=technical,
                    communication_score=communication,
                    completeness_score=completeness,
                    rationale="canned",
                )
            )
        db.flush()
        interview_session_repository.complete(db, session, total_cost_usd=0.1, stop_reason="completed")
        session.completed_at = completed_at
        db.add(session)
        db.commit()
        return session.id
    finally:
        db.close()


def _seed_abandoned_session(user_id: uuid.UUID, plan_id: str, turns: list[tuple[str, float, float, float]]) -> uuid.UUID:
    db = TestSessionLocal()
    try:
        session = interview_session_repository.create(
            db,
            user_id=user_id,
            interview_plan_id=uuid.UUID(plan_id),
            total_questions=len(turns),
            current_difficulty=3,
            topic_queue=[],
            asked_questions=[],
            cost_cap_usd=2.0,
        )
        for idx, (topic, technical, communication, completeness) in enumerate(turns):
            db.add(
                InterviewTurn(
                    session_id=session.id,
                    idx=idx,
                    topic=topic,
                    difficulty=3,
                    question_text=f"Question {idx}",
                    answer_text="an answer",
                    technical_score=technical,
                    communication_score=communication,
                    completeness_score=completeness,
                    rationale="canned",
                )
            )
        db.flush()
        interview_session_repository.abandon(db, session)
        db.commit()
        return session.id
    finally:
        db.close()


def _recompute(user_id: uuid.UUID):
    db = TestSessionLocal()
    try:
        profile = skill_profile_service.recompute_for_user(db, user_id)
        db.commit()
        profile_id = profile.id
    finally:
        db.close()

    db = TestSessionLocal()
    try:
        profile = skill_profile_repository.get_by_user_id(db, user_id)
        _ = list(profile.topic_stats)  # force-load before the session closes below
        return profile
    finally:
        db.close()


def _setup_user_and_plan(client):
    """Returns (access_token, user_id, plan_id) for a fresh signed-up user with a ready plan."""
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    user_id = uuid.UUID(decode_access_token(access_token)["sub"])
    plan = _ready_plan(client, access_token)
    return access_token, user_id, plan["id"]


def test_recompute_single_session_aggregates_correctly(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(
        user_id,
        plan_id,
        [
            ("Python Fundamentals", 8.0, 6.0, 7.0),
            ("Python Fundamentals", 6.0, 6.0, 6.0),
            ("System Design", 4.0, 4.0, 4.0),
        ],
        completed_at=_BASE_TIME,
    )

    profile = _recompute(user_id)

    assert profile.sessions_completed == 1
    assert profile.overall_avg_technical_score == (8.0 + 6.0 + 4.0) / 3
    assert profile.overall_avg_communication_score == (6.0 + 6.0 + 4.0) / 3
    assert profile.overall_avg_completeness_score == (7.0 + 6.0 + 4.0) / 3

    by_key = {t.topic_key: t for t in profile.topic_stats}
    assert set(by_key) == {"python fundamentals", "system design"}

    python_stat = by_key["python fundamentals"]
    assert python_stat.topic_label == "Python Fundamentals"
    assert python_stat.sessions_count == 1
    assert python_stat.turns_count == 2
    assert python_stat.avg_technical_score == 7.0
    assert python_stat.trend == "insufficient_data"
    assert python_stat.previous_session_score is None


def test_recompute_second_session_updates_trend(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(user_id, plan_id, [("Python", 5.0, 5.0, 5.0)], completed_at=_BASE_TIME)
    _recompute(user_id)

    _seed_completed_session(
        user_id, plan_id, [("Python", 8.0, 8.0, 8.0)], completed_at=_BASE_TIME + timedelta(days=7)
    )
    profile = _recompute(user_id)

    assert profile.sessions_completed == 2
    python_stat = next(t for t in profile.topic_stats if t.topic_key == "python")
    assert python_stat.sessions_count == 2
    assert python_stat.turns_count == 2
    assert python_stat.previous_session_score == 5.0
    assert python_stat.last_session_score == 8.0
    assert python_stat.trend == "improving"


def test_recompute_second_session_declining_trend(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(user_id, plan_id, [("Python", 9.0, 9.0, 9.0)], completed_at=_BASE_TIME)
    _recompute(user_id)

    _seed_completed_session(
        user_id, plan_id, [("Python", 3.0, 3.0, 3.0)], completed_at=_BASE_TIME + timedelta(days=7)
    )
    profile = _recompute(user_id)

    python_stat = next(t for t in profile.topic_stats if t.topic_key == "python")
    assert python_stat.trend == "declining"


def test_recompute_ignores_abandoned_sessions(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_abandoned_session(user_id, plan_id, [("Python", 9.0, 9.0, 9.0)])

    profile = _recompute(user_id)

    assert profile.sessions_completed == 0
    assert profile.topic_stats == []


def test_recompute_normalizes_topic_casing(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(user_id, plan_id, [("Python Basics", 6.0, 6.0, 6.0)], completed_at=_BASE_TIME)
    _seed_completed_session(
        user_id, plan_id, [("  python basics  ", 8.0, 8.0, 8.0)], completed_at=_BASE_TIME + timedelta(days=1)
    )

    profile = _recompute(user_id)

    assert len(profile.topic_stats) == 1
    stat = profile.topic_stats[0]
    assert stat.topic_key == "python basics"
    assert stat.sessions_count == 2
    # label reflects the most recently seen original-cased string
    assert stat.topic_label == "  python basics  "


def test_recompute_is_idempotent(client):
    _, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(
        user_id, plan_id, [("Python", 7.0, 7.0, 7.0), ("SQL", 5.0, 5.0, 5.0)], completed_at=_BASE_TIME
    )

    first = _recompute(user_id)
    first_values = {
        "sessions_completed": first.sessions_completed,
        "overall_avg_technical_score": first.overall_avg_technical_score,
        "topics": sorted((t.topic_key, t.sessions_count, t.avg_technical_score, t.trend) for t in first.topic_stats),
    }

    second = _recompute(user_id)
    second_values = {
        "sessions_completed": second.sessions_completed,
        "overall_avg_technical_score": second.overall_avg_technical_score,
        "topics": sorted((t.topic_key, t.sessions_count, t.avg_technical_score, t.trend) for t in second.topic_stats),
    }

    assert first_values == second_values
    assert first.id == second.id  # same profile row reused, not duplicated
