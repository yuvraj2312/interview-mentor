import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: uuid.UUID
    status: str
    original_filename: str
    structured_data: dict | None = None
    low_confidence_fields: list[str] | None = None
    error_message: str | None = None
    created_at: datetime


class ResumeUpdateRequest(BaseModel):
    structured_data: dict
