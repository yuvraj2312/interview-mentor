import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

InterviewPlanFormat = Literal["quick", "standard", "thorough"]


class CreateInterviewPlanRequest(BaseModel):
    skill_gap_analysis_id: uuid.UUID
    format: InterviewPlanFormat


class InterviewPlanOut(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_description_id: uuid.UUID
    skill_gap_analysis_id: uuid.UUID
    format: str
    status: str
    question_count: int | None = None
    topic_mix: list | None = None
    difficulty_min: int | None = None
    difficulty_max: int | None = None
    candidate_level: str | None = None
    rationale: str | None = None
    error_message: str | None = None
    created_at: datetime
