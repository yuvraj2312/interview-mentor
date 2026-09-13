"""JD create + synchronous analysis.

Synchronous (no Arq job) - a single quick LLM call over pasted text, no
file I/O, matching the existing precedent of interview_service.generate_questions
being called inline from POST /sessions. File upload (upload_and_analyze) adds
a local PDF/DOCX text extraction step before the same inline flow - still no
Arq job, since extraction is a fast local parse, not an LLM call: the only
slow step (analyze_job_description) was already inline before this existed.
The original file itself is never persisted - only the extracted text - so
there's no JD-side counterpart to resume_service's storage_key/object-storage
handling.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.agents.jd_analyzer import analyze_job_description
from app.llm_adapter import get_llm_adapter
from app.repositories import job_description_repository
from app.utils.file_parsing import SUPPORTED_CONTENT_TYPES, extract_text


def upload_and_analyze(db: DBSession, *, user_id: uuid.UUID, content_type: str, file_bytes: bytes):
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    raw_text = extract_text(file_bytes, content_type)
    return create_and_analyze(db, user_id=user_id, raw_text=raw_text)


def create_and_analyze(db: DBSession, *, user_id: uuid.UUID, raw_text: str):
    jd = job_description_repository.create(db, user_id=user_id, raw_text=raw_text)
    db.commit()
    db.refresh(jd)

    try:
        llm = get_llm_adapter(db)
        result = analyze_job_description(llm, raw_text)
    except ValueError:
        job_description_repository.update_status(db, jd, status="failed", error_message="LLM returned an unusable response")
        db.commit()
        raise

    job_description_repository.update_status(db, jd, status="ready")
    job_description_repository.update_structured_data(
        db,
        jd,
        structured_data={
            "required_skills": result["required_skills"],
            "preferred_skills": result["preferred_skills"],
            "seniority_level": result["seniority_level"],
        },
        low_confidence_fields=result["low_confidence_fields"],
    )
    db.commit()
    db.refresh(jd)
    return jd
