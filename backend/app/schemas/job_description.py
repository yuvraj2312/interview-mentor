import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateJobDescriptionRequest(BaseModel):
    raw_text: str


class JobDescriptionOut(BaseModel):
    id: uuid.UUID
    status: str
    raw_text: str
    structured_data: dict | None = None
    low_confidence_fields: list[str] | None = None
    error_message: str | None = None
    created_at: datetime


class JobDescriptionUpdateRequest(BaseModel):
    structured_data: dict


class JobDescriptionListItemOut(BaseModel):
    id: uuid.UUID
    status: str
    raw_text_preview: str
    created_at: datetime
