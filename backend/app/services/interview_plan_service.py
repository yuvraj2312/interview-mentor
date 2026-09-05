"""Interview plan create + synchronous generation.

Synchronous (no Arq job), same precedent as job_description_service.create_and_analyze -
a single LLM call over already-extracted structured data, no file I/O.
"""

import uuid

from sqlalchemy.orm import Session as DBSession

from app.agents.interview_planner import generate_interview_plan
from app.llm_adapter import get_llm_adapter
from app.models import JobDescription, Resume, SkillGapAnalysis
from app.repositories import interview_plan_repository

FORMAT_QUESTION_COUNTS = {"quick": 5, "standard": 8, "thorough": 12}


def create_and_generate(
    db: DBSession,
    *,
    user_id: uuid.UUID,
    resume: Resume,
    jd: JobDescription,
    skill_gap_analysis: SkillGapAnalysis,
    format: str,
):
    question_count = FORMAT_QUESTION_COUNTS[format]

    plan = interview_plan_repository.create(
        db,
        user_id=user_id,
        resume_id=resume.id,
        job_description_id=jd.id,
        skill_gap_analysis_id=skill_gap_analysis.id,
        format=format,
    )
    db.commit()
    db.refresh(plan)

    skill_gap = {
        "matched_skills": skill_gap_analysis.matched_skills,
        "missing_required_skills": skill_gap_analysis.missing_required_skills,
        "missing_preferred_skills": skill_gap_analysis.missing_preferred_skills,
    }

    try:
        llm = get_llm_adapter(db)
        result = generate_interview_plan(
            llm,
            resume_data=resume.structured_data,
            jd_data=jd.structured_data,
            skill_gap=skill_gap,
            question_count=question_count,
        )
    except ValueError:
        interview_plan_repository.update_status(
            db, plan, status="failed", error_message="LLM returned an unusable response"
        )
        db.commit()
        raise

    interview_plan_repository.update_plan_data(
        db,
        plan,
        question_count=question_count,
        topic_mix=result["topic_mix"],
        difficulty_min=result["difficulty_min"],
        difficulty_max=result["difficulty_max"],
        candidate_level=result["candidate_level"],
        rationale=result["rationale"],
    )
    db.commit()
    db.refresh(plan)
    return plan
