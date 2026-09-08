from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RoadmapItemResourceOut(BaseModel):
    resource_id: str
    title: str | None
    url: str | None
    resource_type: str | None
    score: float


class RoadmapItemOut(BaseModel):
    topic: str
    gap_description: str
    priority: Literal["high", "medium", "low"]
    recommended_action: str
    resources: list[RoadmapItemResourceOut]


class RoadmapOut(BaseModel):
    status: Literal["pending", "generating", "ready", "failed"]
    summary: str | None
    strengths: list[str] | None
    growth_areas: list[str] | None
    items: list[RoadmapItemOut]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
