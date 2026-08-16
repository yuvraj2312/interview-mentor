import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.models import RefreshToken


def create(db: DBSession, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    db.flush()
    return token


def get_valid_by_hash(db: DBSession, token_hash: str) -> RefreshToken | None:
    token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if token is None:
        return None
    if token.revoked_at is not None:
        return None
    if token.expires_at < datetime.now(timezone.utc):
        return None
    return token


def get_by_hash(db: DBSession, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def revoke(db: DBSession, token: RefreshToken) -> None:
    token.revoked_at = datetime.now(timezone.utc)
    db.flush()
