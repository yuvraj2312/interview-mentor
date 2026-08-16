import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import Session as SessionModel


def create(db: DBSession, *, user_id: uuid.UUID, resume_text: str, jd_text: str) -> SessionModel:
    session = SessionModel(user_id=user_id, resume_text=resume_text, jd_text=jd_text)
    db.add(session)
    db.flush()
    return session


def get_by_id_for_user(db: DBSession, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel | None:
    return (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.user_id == user_id)
        .first()
    )
