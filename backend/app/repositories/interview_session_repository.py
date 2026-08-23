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
) -> InterviewSession:
    session = InterviewSession(
        user_id=user_id,
        interview_plan_id=interview_plan_id,
        total_questions=total_questions,
        current_difficulty=current_difficulty,
        topic_queue=topic_queue,
        asked_questions=asked_questions,
    )
    db.add(session)
    db.flush()
    return session


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
) -> InterviewSession:
    session.current_turn_index += 1
    session.current_difficulty = current_difficulty
    session.topic_queue = topic_queue
    session.asked_questions = asked_questions
    db.add(session)
    db.flush()
    return session


def complete(db: DBSession, session: InterviewSession) -> InterviewSession:
    session.status = "complete"
    session.completed_at = datetime.now(timezone.utc)
    db.add(session)
    db.flush()
    return session
