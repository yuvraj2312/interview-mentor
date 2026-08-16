import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import User


def get_by_email(db: DBSession, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: DBSession, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create(db: DBSession, *, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.flush()
    return user
