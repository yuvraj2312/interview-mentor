import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.embedding_adapter import get_embedding_adapter
from app.models import SkillGapAnalysis, User
from app.repositories import job_description_repository, resume_repository, skill_gap_repository
from app.schemas.skill_gap import ComputeSkillGapRequest, SkillGapOut
from app.services import skill_gap_service

router = APIRouter()


def _to_out(analysis: SkillGapAnalysis) -> SkillGapOut:
    return SkillGapOut(
        id=analysis.id,
        resume_id=analysis.resume_id,
        job_description_id=analysis.job_description_id,
        matched_skills=analysis.matched_skills,
        missing_required_skills=analysis.missing_required_skills,
        missing_preferred_skills=analysis.missing_preferred_skills,
        match_score=analysis.match_score,
        created_at=analysis.created_at,
    )


@router.post("", response_model=SkillGapOut, status_code=201)
def compute_skill_gap(
    payload: ComputeSkillGapRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillGapOut:
    resume = resume_repository.get_by_id_for_user(db, payload.resume_id, current_user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != "ready":
        raise HTTPException(status_code=400, detail="Resume is not ready")

    jd = job_description_repository.get_by_id_for_user(db, payload.job_description_id, current_user.id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    if jd.status != "ready":
        raise HTTPException(status_code=400, detail="Job description is not ready")

    result = skill_gap_service.compute(resume, jd, get_embedding_adapter())
    analysis = skill_gap_repository.create(
        db,
        user_id=current_user.id,
        resume_id=resume.id,
        job_description_id=jd.id,
        **result,
    )
    db.commit()
    db.refresh(analysis)
    return _to_out(analysis)


@router.get("/{skill_gap_id}", response_model=SkillGapOut)
def get_skill_gap(
    skill_gap_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillGapOut:
    analysis = skill_gap_repository.get_by_id_for_user(db, skill_gap_id, current_user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")
    return _to_out(analysis)
