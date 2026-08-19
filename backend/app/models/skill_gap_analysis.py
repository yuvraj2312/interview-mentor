import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_descriptions.id"), nullable=False, index=True
    )
    matched_skills: Mapped[list] = mapped_column(JSONB)
    missing_required_skills: Mapped[list] = mapped_column(JSONB)
    missing_preferred_skills: Mapped[list] = mapped_column(JSONB)
    match_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
