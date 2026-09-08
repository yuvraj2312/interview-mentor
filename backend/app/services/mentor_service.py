"""Mentor / roadmap generation (Phase 6c).

generate_roadmap_for_session is called only from the arq worker (see
app/background/tasks.py::generate_roadmap), never from a request handler -
the Mentor agent's LLM call plus per-gap embedding/vector-search work is
exactly the kind of long-running AI work CLAUDE.md says must not run
inline (same reasoning as resume_service.process_uploaded_resume, unlike
skill_profile_service.recompute_for_user which has no LLM/embedding call
and stays inline).

One Roadmap row is created per completed session, not recomputed in place
per user like SkillProfile - see app/models/roadmap.py's docstring for why.
"""

import uuid

from sqlalchemy.orm import Session as DBSession

from app.agents.mentor import generate_roadmap
from app.core.config import settings
from app.embedding_adapter import get_embedding_adapter
from app.llm_adapter import get_llm_adapter
from app.models import InterviewSession, RoadmapItem
from app.repositories import (
    interview_plan_repository,
    interview_session_repository,
    roadmap_repository,
    skill_gap_repository,
    skill_profile_repository,
)
from app.services import vector_store_service


def _turns_payload(session: InterviewSession) -> list[dict]:
    return [
        {
            "topic": turn.topic,
            "difficulty": turn.difficulty,
            "question_text": turn.question_text,
            "answer_text": turn.answer_text,
            "technical_score": turn.technical_score,
            "communication_score": turn.communication_score,
            "completeness_score": turn.completeness_score,
            "rationale": turn.rationale,
        }
        for turn in session.turns
    ]


def _skill_profile_payload(db: DBSession, user_id: uuid.UUID) -> dict:
    profile = skill_profile_repository.get_by_user_id(db, user_id)
    if profile is None:
        return {}
    return {
        "sessions_completed": profile.sessions_completed,
        "overall_avg_technical_score": profile.overall_avg_technical_score,
        "overall_avg_communication_score": profile.overall_avg_communication_score,
        "overall_avg_completeness_score": profile.overall_avg_completeness_score,
        "topics": [
            {
                "topic": stat.topic_label,
                "sessions_count": stat.sessions_count,
                "avg_technical_score": stat.avg_technical_score,
                "avg_communication_score": stat.avg_communication_score,
                "avg_completeness_score": stat.avg_completeness_score,
                "trend": stat.trend,
            }
            for stat in profile.topic_stats
        ],
    }


def _missing_skills(db: DBSession, session: InterviewSession) -> list[str]:
    plan = interview_plan_repository.get_by_id(db, session.interview_plan_id)
    if plan is None:
        return []
    skill_gap = skill_gap_repository.get_by_id(db, plan.skill_gap_analysis_id)
    if skill_gap is None:
        return []
    return [*skill_gap.missing_required_skills, *skill_gap.missing_preferred_skills]


def _match_resources(embedding_adapter, topic: str, gap_description: str) -> list[dict]:
    query_vector = embedding_adapter.embed([f"{topic}: {gap_description}"])[0]
    hits = vector_store_service.search(
        settings.qdrant_learning_resources_collection,
        query_vector,
        limit=3,
        score_threshold=settings.learning_resource_similarity_threshold,
    )
    return [
        {
            # payload["resource_id"] is the human-readable seed slug (see
            # app/data/learning_resources_seed.py); hit["id"] is the
            # uuid5-derived Qdrant point id, not meant for display.
            "resource_id": hit["payload"].get("resource_id", str(hit["id"])),
            "title": hit["payload"].get("title"),
            "url": hit["payload"].get("url"),
            "resource_type": hit["payload"].get("resource_type"),
            "score": hit["score"],
        }
        for hit in hits
    ]


def generate_roadmap_for_session(db: DBSession, session_id: uuid.UUID) -> None:
    session = interview_session_repository.get_by_id(db, session_id)
    if session is None:
        return

    roadmap = roadmap_repository.create(db, user_id=session.user_id, session_id=session.id)
    db.commit()

    try:
        turns = _turns_payload(session)
        skill_profile = _skill_profile_payload(db, session.user_id)
        missing_skills = _missing_skills(db, session)

        llm = get_llm_adapter(db, session_id=session.id)
        result = generate_roadmap(llm, turns=turns, skill_profile=skill_profile, missing_skills=missing_skills)
        db.commit()

        embedding_adapter = get_embedding_adapter()
        items = []
        for item in result["roadmap_items"]:
            matched_resources = _match_resources(embedding_adapter, item["topic"], item["gap_description"])
            items.append(
                RoadmapItem(
                    topic=item["topic"],
                    gap_description=item["gap_description"],
                    priority=item["priority"],
                    recommended_action=item["recommended_action"],
                    matched_resources=matched_resources,
                )
            )

        roadmap_repository.mark_ready(
            db,
            roadmap,
            summary=result["summary"],
            strengths=result["strengths"],
            growth_areas=result["growth_areas"],
            items=items,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        roadmap = roadmap_repository.get_by_id(db, roadmap.id)
        if roadmap is not None:
            roadmap_repository.mark_failed(db, roadmap, error_message=str(exc))
            db.commit()
