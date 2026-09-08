import uuid

from app.db import SessionLocal
from app.services import mentor_service, resume_service


async def process_resume_upload(ctx, resume_id: str) -> None:
    # Worker runs in a separate process from the API - can't reuse the
    # request-scoped get_db() generator, so open/close our own session.
    db = SessionLocal()
    try:
        resume_service.process_uploaded_resume(db, uuid.UUID(resume_id))
    finally:
        db.close()


async def generate_roadmap(ctx, session_id: str) -> None:
    db = SessionLocal()
    try:
        mentor_service.generate_roadmap_for_session(db, uuid.UUID(session_id))
    finally:
        db.close()
