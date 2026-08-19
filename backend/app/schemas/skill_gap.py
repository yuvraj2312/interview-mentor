import uuid
from datetime import datetime

from pydantic import BaseModel


class ComputeSkillGapRequest(BaseModel):
    resume_id: uuid.UUID
    job_description_id: uuid.UUID


class SkillGapOut(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_description_id: uuid.UUID
    matched_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    match_score: float
    created_at: datetime
