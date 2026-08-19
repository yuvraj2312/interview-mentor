import uuid

import jwt
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db import get_db
from app.models import User
from app.repositories import user_repository

bearer_scheme = HTTPBearer(auto_error=False)

_arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    # Lazy singleton rather than a FastAPI lifespan hook: tests/conftest.py
    # instantiates TestClient(app) directly (not as a context manager),
    # which doesn't reliably fire lifespan startup/shutdown.
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _arq_pool


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: DBSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc

    if payload.get("type") != "access":
        raise unauthorized

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError as exc:
        raise unauthorized from exc

    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise unauthorized
    return user
