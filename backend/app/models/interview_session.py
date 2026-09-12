import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    interview_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_plans.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    current_turn_index: Mapped[int] = mapped_column(Integer, default=0)
    # CE-c: 1-based ordinal of the current main-topic slot - distinct from
    # current_turn_index (total exchanges, which can now exceed
    # total_questions once follow-ups exist). Old rows default to 0; only
    # meaningful while a session is actively in progress.
    topic_number: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_questions: Mapped[int] = mapped_column(Integer)
    current_difficulty: Mapped[int] = mapped_column(Integer)
    topic_queue: Mapped[list] = mapped_column(JSONB)
    asked_questions: Mapped[list] = mapped_column(JSONB)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_cap_usd: Mapped[float] = mapped_column(Float)
    stop_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    turns: Mapped[list["InterviewTurn"]] = relationship(
        back_populates="session", order_by="InterviewTurn.idx", cascade="all, delete-orphan"
    )


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False, index=True)
    idx: Mapped[int] = mapped_column(Integer)
    topic: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    # CE-c: persisted (unlike the live-only follow-up budget counter) because
    # the finished-session transcript is built entirely from these rows and
    # has no access to Redis's ephemeral live state. topic_number is
    # nullable - old rows predate CE-c and have no accurate value to backfill.
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    topic_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followup_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["InterviewSession"] = relationship(back_populates="turns")
