import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.models import InterviewPlan, User
from app.repositories import interview_plan_repository, job_description_repository, resume_repository, skill_gap_repository
from app.schemas.interview_plan import CreateInterviewPlanRequest, InterviewPlanOut
from app.services import interview_plan_service

router = APIRouter()


def _to_out(plan: InterviewPlan) -> InterviewPlanOut:
    return InterviewPlanOut(
        id=plan.id,
        resume_id=plan.resume_id,
        job_description_id=plan.job_description_id,
        skill_gap_analysis_id=plan.skill_gap_analysis_id,
        format=plan.format,
        status=plan.status,
        question_count=plan.question_count,
        topic_mix=plan.topic_mix,
        difficulty_min=plan.difficulty_min,
        difficulty_max=plan.difficulty_max,
        candidate_level=plan.candidate_level,
        rationale=plan.rationale,
        error_message=plan.error_message,
        created_at=plan.created_at,
    )


@router.post("", response_model=InterviewPlanOut, status_code=201)
def create_interview_plan(
    payload: CreateInterviewPlanRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewPlanOut:
    skill_gap_analysis = skill_gap_repository.get_by_id_for_user(db, payload.skill_gap_analysis_id, current_user.id)
    if skill_gap_analysis is None:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")

    resume = resume_repository.get_by_id_for_user(db, skill_gap_analysis.resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != "ready":
        raise HTTPException(status_code=400, detail="Resume is not ready")

    jd = job_description_repository.get_by_id_for_user(db, skill_gap_analysis.job_description_id, current_user.id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    if jd.status != "ready":
        raise HTTPException(status_code=400, detail="Job description is not ready")

    try:
        plan = interview_plan_service.create_and_generate(
            db,
            user_id=current_user.id,
            resume=resume,
            jd=jd,
            skill_gap_analysis=skill_gap_analysis,
            format=payload.format,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc
    return _to_out(plan)


@router.get("/{plan_id}", response_model=InterviewPlanOut)
def get_interview_plan(
    plan_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewPlanOut:
    plan = interview_plan_repository.get_by_id_for_user(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Interview plan not found")
    return _to_out(plan)
