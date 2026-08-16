from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse
from app.services import auth_service

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    return auth_service.signup(db, email=payload.email, password=payload.password)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    return auth_service.login(db, email=payload.email, password=payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    return auth_service.refresh(db, raw_refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: DBSession = Depends(get_db)) -> None:
    auth_service.logout(db, raw_refresh_token=payload.refresh_token)
