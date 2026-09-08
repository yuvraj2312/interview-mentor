import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.models import InterviewSession


def create(
    db: DBSession,
    *,
    user_id: uuid.UUID,
    interview_plan_id: uuid.UUID,
    total_questions: int,
    current_difficulty: int,
    topic_queue: list,
    asked_questions: list,
    cost_cap_usd: float,
    total_cost_usd: float = 0.0,
) -> InterviewSession:
    session = InterviewSession(
        user_id=user_id,
        interview_plan_id=interview_plan_id,
        total_questions=total_questions,
        current_difficulty=current_difficulty,
        topic_queue=topic_queue,
        asked_questions=asked_questions,
        cost_cap_usd=cost_cap_usd,
        total_cost_usd=total_cost_usd,
    )
    db.add(session)
    db.flush()
    return session


def get_by_id(db: DBSession, session_id: uuid.UUID) -> InterviewSession | None:
    return db.query(InterviewSession).filter(InterviewSession.id == session_id).first()


def get_by_id_for_user(db: DBSession, session_id: uuid.UUID, user_id: uuid.UUID) -> InterviewSession | None:
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
        .first()
    )


def advance(
    db: DBSession,
    session: InterviewSession,
    *,
    current_difficulty: int,
    topic_queue: list,
    asked_questions: list,
    total_cost_usd: float,
) -> InterviewSession:
    session.current_turn_index += 1
    session.current_difficulty = current_difficulty
    session.topic_queue = topic_queue
    session.asked_questions = asked_questions
    session.total_cost_usd = total_cost_usd
    session.last_activity_at = datetime.now(timezone.utc)
    db.add(session)
    db.flush()
    return session


def complete(
    db: DBSession, session: InterviewSession, *, total_cost_usd: float, stop_reason: str
) -> InterviewSession:
    now = datetime.now(timezone.utc)
    session.status = "complete"
    session.completed_at = now
    session.last_activity_at = now
    session.total_cost_usd = total_cost_usd
    session.stop_reason = stop_reason
    db.add(session)
    db.flush()
    return session


def abandon(db: DBSession, session: InterviewSession) -> InterviewSession:
    # Deliberately does not touch last_activity_at: that timestamp is the
    # evidence the inactivity timeout was exceeded, and overwriting it with
    # "now" at detection time would erase when the candidate actually went
    # idle.
    session.status = "abandoned"
    db.add(session)
    db.flush()
    return session
