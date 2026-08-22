import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InterviewPlan(Base):
    __tablename__ = "interview_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_descriptions.id"), nullable=False, index=True
    )
    skill_gap_analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill_gap_analyses.id"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_mix: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    difficulty_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
