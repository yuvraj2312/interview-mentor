"""Unauthenticated health check for uptime monitoring / load balancers.

Deliberately excludes get_current_user (see app/core/deps.py) - a health
check that requires auth can't be used by an external monitor that doesn't
have credentials.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from app.core.redis_client import get_redis_client
from app.db import get_db

router = APIRouter()
logger = logging.getLogger("app.api.health")


def _check_database(db: DBSession) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Health check: database unreachable", exc_info=True)
        return False


def _check_redis() -> bool:
    try:
        get_redis_client().ping()
        return True
    except Exception:
        logger.warning("Health check: redis unreachable", exc_info=True)
        return False


@router.get("")
def get_health(db: DBSession = Depends(get_db)) -> JSONResponse:
    db_ok = _check_database(db)
    redis_ok = _check_redis()
    healthy = db_ok and redis_ok
    body = {
        "status": "ok" if healthy else "error",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)
