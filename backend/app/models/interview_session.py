import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
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
    total_questions: Mapped[int] = mapped_column(Integer)
    current_difficulty: Mapped[int] = mapped_column(Integer)
    topic_queue: Mapped[list] = mapped_column(JSONB)
    asked_questions: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["InterviewSession"] = relationship(back_populates="turns")
