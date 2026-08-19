import uuid

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_arq_pool, get_current_user
from app.db import get_db
from app.models import Resume, User
from app.repositories import resume_repository
from app.schemas.resume import ResumeOut, ResumeUpdateRequest
from app.services import resume_service

router = APIRouter()


def _get_resume_or_404(db: DBSession, resume_id: uuid.UUID, user_id: uuid.UUID) -> Resume:
    resume = resume_repository.get_by_id_for_user(db, resume_id, user_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


def _to_out(resume: Resume) -> ResumeOut:
    return ResumeOut(
        id=resume.id,
        status=resume.status,
        original_filename=resume.original_filename,
        structured_data=resume.structured_data,
        low_confidence_fields=resume.low_confidence_fields,
        error_message=resume.error_message,
        created_at=resume.created_at,
    )


@router.post("", response_model=ResumeOut, status_code=202)
async def upload_resume(
    file: UploadFile,
    db: DBSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    current_user: User = Depends(get_current_user),
) -> ResumeOut:
    file_bytes = await file.read()
    resume = await resume_service.initiate_upload(
        db,
        arq_pool,
        user_id=current_user.id,
        filename=file.filename or "resume",
        content_type=file.content_type or "",
        file_bytes=file_bytes,
    )
    return _to_out(resume)


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeOut:
    resume = _get_resume_or_404(db, resume_id, current_user.id)
    return _to_out(resume)


@router.patch("/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: uuid.UUID,
    payload: ResumeUpdateRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeOut:
    resume = _get_resume_or_404(db, resume_id, current_user.id)
    if resume.status != "ready":
        raise HTTPException(status_code=400, detail="Resume is not ready for review")

    resume_repository.update_structured_data(db, resume, structured_data=payload.structured_data)
    db.commit()
    db.refresh(resume)
    return _to_out(resume)
