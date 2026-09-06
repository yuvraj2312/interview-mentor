from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SkillProfileTopicStatOut(BaseModel):
    topic: str
    sessions_count: int
    avg_technical_score: float
    avg_communication_score: float
    avg_completeness_score: float
    trend: Literal["improving", "declining", "stable", "insufficient_data"]


class SkillProfileOut(BaseModel):
    sessions_completed: int
    overall_avg_technical_score: float | None
    overall_avg_communication_score: float | None
    overall_avg_completeness_score: float | None
    updated_at: datetime
    topics: list[SkillProfileTopicStatOut]
