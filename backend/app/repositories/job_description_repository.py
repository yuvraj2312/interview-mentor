import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import JobDescription


def create(db: DBSession, *, user_id: uuid.UUID, raw_text: str) -> JobDescription:
    jd = JobDescription(user_id=user_id, raw_text=raw_text)
    db.add(jd)
    db.flush()
    return jd


def get_by_id_for_user(db: DBSession, jd_id: uuid.UUID, user_id: uuid.UUID) -> JobDescription | None:
    return db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.user_id == user_id).first()


def list_for_user(db: DBSession, user_id: uuid.UUID, limit: int = 50) -> list[JobDescription]:
    return (
        db.query(JobDescription)
        .filter(JobDescription.user_id == user_id)
        .order_by(JobDescription.created_at.desc())
        .limit(limit)
        .all()
    )


def update_status(
    db: DBSession, jd: JobDescription, *, status: str, error_message: str | None = None
) -> JobDescription:
    jd.status = status
    jd.error_message = error_message
    db.add(jd)
    db.flush()
    return jd


def update_structured_data(
    db: DBSession, jd: JobDescription, *, structured_data: dict, low_confidence_fields: list | None = None
) -> JobDescription:
    jd.structured_data = structured_data
    jd.low_confidence_fields = low_confidence_fields if low_confidence_fields is not None else []
    db.add(jd)
    db.flush()
    return jd
