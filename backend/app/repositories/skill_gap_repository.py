import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import SkillGapAnalysis


def create(
    db: DBSession,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
    matched_skills: list,
    missing_required_skills: list,
    missing_preferred_skills: list,
    match_score: float,
) -> SkillGapAnalysis:
    analysis = SkillGapAnalysis(
        user_id=user_id,
        resume_id=resume_id,
        job_description_id=job_description_id,
        matched_skills=matched_skills,
        missing_required_skills=missing_required_skills,
        missing_preferred_skills=missing_preferred_skills,
        match_score=match_score,
    )
    db.add(analysis)
    db.flush()
    return analysis


def get_by_id(db: DBSession, skill_gap_id: uuid.UUID) -> SkillGapAnalysis | None:
    return db.query(SkillGapAnalysis).filter(SkillGapAnalysis.id == skill_gap_id).first()


def get_by_id_for_user(db: DBSession, skill_gap_id: uuid.UUID, user_id: uuid.UUID) -> SkillGapAnalysis | None:
    return (
        db.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.id == skill_gap_id, SkillGapAnalysis.user_id == user_id)
        .first()
    )
