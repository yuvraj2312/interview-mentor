import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SkillProfile(Base):
    """One row per candidate: the current, fully-recomputed cross-session
    aggregate. Recomputed from scratch (not incrementally updated) every
    time one of the user's interview sessions completes - see
    app/services/skill_profile_service.py.
    """

    __tablename__ = "skill_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0)
    overall_avg_technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_avg_communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_avg_completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    topic_stats: Mapped[list["SkillProfileTopicStat"]] = relationship(
        back_populates="skill_profile", cascade="all, delete-orphan"
    )


class SkillProfileTopicStat(Base):
    """Per-topic aggregate within a SkillProfile. topic_key is a
    case/whitespace-normalized grouping key (see skill_profile_service.py);
    two differently-phrased topic strings describing the same underlying
    skill are NOT merged - see docs/architecture.md's Phase 6b note.
    """

    __tablename__ = "skill_profile_topic_stats"
    __table_args__ = (UniqueConstraint("skill_profile_id", "topic_key", name="uq_skill_profile_topic"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skill_profiles.id"), nullable=False, index=True)
    topic_key: Mapped[str] = mapped_column(String(255))
    topic_label: Mapped[str] = mapped_column(String(255))
    sessions_count: Mapped[int] = mapped_column(Integer)
    turns_count: Mapped[int] = mapped_column(Integer)
    avg_technical_score: Mapped[float] = mapped_column(Float)
    avg_communication_score: Mapped[float] = mapped_column(Float)
    avg_completeness_score: Mapped[float] = mapped_column(Float)
    last_session_score: Mapped[float] = mapped_column(Float)
    previous_session_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    skill_profile: Mapped["SkillProfile"] = relationship(back_populates="topic_stats")
