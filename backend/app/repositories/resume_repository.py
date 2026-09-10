import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import Resume


def create(
    db: DBSession, *, user_id: uuid.UUID, original_filename: str, content_type: str, storage_key: str = ""
) -> Resume:
    resume = Resume(
        user_id=user_id,
        original_filename=original_filename,
        content_type=content_type,
        storage_key=storage_key,
    )
    db.add(resume)
    db.flush()
    return resume


def get_by_id_for_user(db: DBSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> Resume | None:
    return db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()


def list_for_user(db: DBSession, user_id: uuid.UUID, limit: int = 50) -> list[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .limit(limit)
        .all()
    )


def get_by_id(db: DBSession, resume_id: uuid.UUID) -> Resume | None:
    return db.query(Resume).filter(Resume.id == resume_id).first()


def update_status(db: DBSession, resume: Resume, *, status: str, error_message: str | None = None) -> Resume:
    resume.status = status
    resume.error_message = error_message
    db.add(resume)
    db.flush()
    return resume


def update_extracted(
    db: DBSession,
    resume: Resume,
    *,
    extracted_text: str,
    structured_data: dict,
    low_confidence_fields: list,
    status: str = "ready",
) -> Resume:
    resume.extracted_text = extracted_text
    resume.structured_data = structured_data
    resume.low_confidence_fields = low_confidence_fields
    resume.status = status
    db.add(resume)
    db.flush()
    return resume


def update_structured_data(db: DBSession, resume: Resume, *, structured_data: dict) -> Resume:
    resume.structured_data = structured_data
    resume.low_confidence_fields = []
    db.add(resume)
    db.flush()
    return resume
