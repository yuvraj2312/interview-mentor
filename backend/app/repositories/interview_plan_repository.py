import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import InterviewPlan


def create(
    db: DBSession,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
    skill_gap_analysis_id: uuid.UUID,
    format: str,
) -> InterviewPlan:
    plan = InterviewPlan(
        user_id=user_id,
        resume_id=resume_id,
        job_description_id=job_description_id,
        skill_gap_analysis_id=skill_gap_analysis_id,
        format=format,
    )
    db.add(plan)
    db.flush()
    return plan


def get_by_id_for_user(db: DBSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> InterviewPlan | None:
    return db.query(InterviewPlan).filter(InterviewPlan.id == plan_id, InterviewPlan.user_id == user_id).first()


def update_status(db: DBSession, plan: InterviewPlan, *, status: str, error_message: str | None = None) -> InterviewPlan:
    plan.status = status
    plan.error_message = error_message
    db.add(plan)
    db.flush()
    return plan


def update_plan_data(
    db: DBSession,
    plan: InterviewPlan,
    *,
    question_count: int,
    topic_mix: list,
    difficulty_min: int,
    difficulty_max: int,
    candidate_level: str,
    rationale: str,
) -> InterviewPlan:
    plan.question_count = question_count
    plan.topic_mix = topic_mix
    plan.difficulty_min = difficulty_min
    plan.difficulty_max = difficulty_max
    plan.candidate_level = candidate_level
    plan.rationale = rationale
    plan.status = "ready"
    db.add(plan)
    db.flush()
    return plan
