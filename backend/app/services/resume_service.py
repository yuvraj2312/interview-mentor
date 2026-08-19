"""Resume upload + background processing orchestration.

initiate_upload is called from the API route (fast path: store the file,
enqueue a job, return). process_uploaded_resume is called from the Arq
worker (app/background/tasks.py), never from a request handler - resume
parsing/extraction must not block the request/response cycle.
"""

import uuid

from arq import ArqRedis
from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.agents.resume_analyzer import analyze_resume
from app.llm_adapter import get_llm_adapter
from app.repositories import resume_repository
from app.storage import build_resume_object_key, download_resume_file, upload_resume_file
from app.utils.file_parsing import extract_text

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def initiate_upload(
    db: DBSession,
    arq_pool: ArqRedis,
    *,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    file_bytes: bytes,
):
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    resume = resume_repository.create(
        db, user_id=user_id, original_filename=filename, content_type=content_type
    )

    key = build_resume_object_key(user_id, resume.id, filename)
    upload_resume_file(file_bytes, key, content_type)
    resume.storage_key = key
    db.add(resume)
    db.commit()
    db.refresh(resume)

    await arq_pool.enqueue_job("process_resume_upload", str(resume.id))
    return resume


def process_uploaded_resume(db: DBSession, resume_id: uuid.UUID) -> None:
    resume = resume_repository.get_by_id(db, resume_id)
    if resume is None:
        return

    try:
        resume_repository.update_status(db, resume, status="parsing")
        db.commit()

        file_bytes = download_resume_file(resume.storage_key)
        text = extract_text(file_bytes, resume.content_type)

        resume_repository.update_status(db, resume, status="analyzing")
        db.commit()

        llm = get_llm_adapter()
        result = analyze_resume(llm, text)

        resume_repository.update_extracted(
            db,
            resume,
            extracted_text=text,
            structured_data={
                "skills": result["skills"],
                "experience": result["experience"],
                "education": result["education"],
                "projects": result["projects"],
            },
            low_confidence_fields=result["low_confidence_fields"],
            status="ready",
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        resume = resume_repository.get_by_id(db, resume_id)
        if resume is not None:
            resume_repository.update_status(db, resume, status="failed", error_message=str(exc))
            db.commit()
