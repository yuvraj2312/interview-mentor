import os
import uuid

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db as db_module
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.db import Base, get_db
from app.main import app

TEST_REDIS_KEY_PREFIX = "interview_mentor_test"

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    settings.database_url.rsplit("/", 1)[0] + "/interview_mentor_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(autouse=True)
def _redis_namespace(monkeypatch):
    monkeypatch.setattr(settings, "redis_key_prefix", TEST_REDIS_KEY_PREFIX)
    yield
    client = get_redis_client()
    for key in client.scan_iter(f"{TEST_REDIS_KEY_PREFIX}:*"):
        client.delete(key)


@pytest.fixture()
def redis_client():
    return get_redis_client()


@pytest.fixture(autouse=True)
def _ws_db_override(monkeypatch):
    # The WebSocket handler can't use Depends(get_db) (see
    # app/websockets/interview_session_ws.py's module docstring) - it opens
    # app.db.SessionLocal() manually per operation, so tests need that
    # attribute itself pointed at the test database.
    monkeypatch.setattr(db_module, "SessionLocal", TestSessionLocal)


@pytest.fixture()
def client():
    def _get_test_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)

    # The lazy Arq pool singleton binds to the event loop it was created
    # on; TestClient uses a fresh loop per test, so a pool created in one
    # test would raise "Event loop is closed" if reused in the next.
    import app.core.deps as deps_module

    deps_module._arq_pool = None


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def signup_and_get_tokens(client: TestClient, email: str | None = None, password: str = "hunter2pass") -> dict:
    email = email or unique_email()
    response = client.post("/auth/signup", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()
