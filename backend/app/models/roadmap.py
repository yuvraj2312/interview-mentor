import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Roadmap(Base):
    """One row per completed session, not one row per user. Unlike
    SkillProfile's full-recompute-every-time, a roadmap's feedback is
    evidence tied to a specific session's transcript (CLAUDE.md's Mentor
    guardrail: "specific and evidence-based, not generic") - overwriting
    it in place on the next session would destroy that evidence trail. See
    app/services/mentor_service.py.
    """

    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    growth_areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["RoadmapItem"]] = relationship(back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roadmaps.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255))
    gap_description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    recommended_action: Mapped[str] = mapped_column(Text)
    # Denormalized snapshot of the learning_resources search hits at
    # generation time - [{resource_id, title, url, resource_type, score}, ...].
    # Not a FK to a resources table: the vector store is the source of truth
    # for current content, but the roadmap should preserve what was actually
    # recommended even if that content later changes or is removed.
    matched_resources: Mapped[list] = mapped_column(JSONB, default=list)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="items")
