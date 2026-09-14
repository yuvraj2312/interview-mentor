import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models import User
from app.repositories import refresh_token_repository, user_repository
from app.schemas.auth import TokenResponse


def _issue_token_pair(
    db: DBSession,
    user: User,
    *,
    session_id: uuid.UUID | None = None,
    session_started_at: datetime | None = None,
) -> TokenResponse:
    access_token = create_access_token(user.id)
    raw_refresh_token = generate_refresh_token()
    refresh_token_repository.create(
        db,
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=refresh_token_expiry(),
        session_id=session_id,
        session_started_at=session_started_at,
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh_token)


def signup(db: DBSession, *, email: str, password: str) -> TokenResponse:
    if user_repository.get_by_email(db, email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = user_repository.create(db, email=email, hashed_password=hash_password(password))
    return _issue_token_pair(db, user)


def login(db: DBSession, *, email: str, password: str) -> TokenResponse:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise unauthorized

    return _issue_token_pair(db, user)


def refresh(db: DBSession, *, raw_refresh_token: str) -> TokenResponse:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    token = refresh_token_repository.get_valid_by_hash(db, hash_refresh_token(raw_refresh_token))
    if token is None:
        raise unauthorized

    user = user_repository.get_by_id(db, token.user_id)
    if user is None:
        raise unauthorized

    session_age = datetime.now(timezone.utc) - token.session_started_at
    if session_age > timedelta(hours=settings.absolute_session_max_hours):
        refresh_token_repository.revoke(db, token)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again")

    refresh_token_repository.revoke(db, token)
    # Carry the original session's identity forward so rotation never resets
    # the absolute-cap clock (see the docstring-style comment on
    # Settings.absolute_session_max_hours).
    return _issue_token_pair(db, user, session_id=token.session_id, session_started_at=token.session_started_at)


def logout(db: DBSession, *, raw_refresh_token: str) -> None:
    token = refresh_token_repository.get_by_hash(db, hash_refresh_token(raw_refresh_token))
    if token is not None and token.revoked_at is None:
        refresh_token_repository.revoke(db, token)
    db.commit()
