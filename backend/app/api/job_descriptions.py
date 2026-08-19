import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.models import JobDescription, User
from app.repositories import job_description_repository
from app.schemas.job_description import CreateJobDescriptionRequest, JobDescriptionOut, JobDescriptionUpdateRequest
from app.services import job_description_service

router = APIRouter()


def _get_jd_or_404(db: DBSession, jd_id: uuid.UUID, user_id: uuid.UUID) -> JobDescription:
    jd = job_description_repository.get_by_id_for_user(db, jd_id, user_id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


def _to_out(jd: JobDescription) -> JobDescriptionOut:
    return JobDescriptionOut(
        id=jd.id,
        status=jd.status,
        raw_text=jd.raw_text,
        structured_data=jd.structured_data,
        low_confidence_fields=jd.low_confidence_fields,
        error_message=jd.error_message,
        created_at=jd.created_at,
    )


@router.post("", response_model=JobDescriptionOut, status_code=201)
def create_job_description(
    payload: CreateJobDescriptionRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescriptionOut:
    try:
        jd = job_description_service.create_and_analyze(db, user_id=current_user.id, raw_text=payload.raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc
    return _to_out(jd)


@router.get("/{jd_id}", response_model=JobDescriptionOut)
def get_job_description(
    jd_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescriptionOut:
    jd = _get_jd_or_404(db, jd_id, current_user.id)
    return _to_out(jd)


@router.patch("/{jd_id}", response_model=JobDescriptionOut)
def update_job_description(
    jd_id: uuid.UUID,
    payload: JobDescriptionUpdateRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescriptionOut:
    jd = _get_jd_or_404(db, jd_id, current_user.id)
    if jd.status != "ready":
        raise HTTPException(status_code=400, detail="Job description is not ready for review")

    job_description_repository.update_structured_data(db, jd, structured_data=payload.structured_data)
    db.commit()
    db.refresh(jd)
    return _to_out(jd)
