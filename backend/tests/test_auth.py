from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import hash_refresh_token
from app.models import RefreshToken
from tests.conftest import TestSessionLocal, signup_and_get_tokens, unique_email


def test_signup_returns_token_pair(client):
    tokens = signup_and_get_tokens(client)
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_signup_duplicate_email_conflicts(client):
    email = unique_email()
    signup_and_get_tokens(client, email=email)
    response = client.post("/auth/signup", json={"email": email, "password": "another-pass"})
    assert response.status_code == 409


def test_login_happy_path(client):
    email = unique_email()
    signup_and_get_tokens(client, email=email, password="correct-horse")
    response = client.post("/auth/login", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_unauthorized(client):
    email = unique_email()
    signup_and_get_tokens(client, email=email, password="correct-horse")
    response = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401


def test_refresh_rotates_token_and_old_token_then_fails(client):
    tokens = signup_and_get_tokens(client)
    old_refresh = tokens["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != old_refresh

    reuse = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401

    still_valid = client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert still_valid.status_code == 200


def test_logout_then_refresh_fails(client):
    tokens = signup_and_get_tokens(client)
    logout = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 204

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def _backdate_session_start(raw_refresh_token: str, when: datetime) -> None:
    db = TestSessionLocal()
    try:
        token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == hash_refresh_token(raw_refresh_token))
            .one()
        )
        token.session_started_at = when
        db.commit()
    finally:
        db.close()


def test_refresh_beyond_absolute_session_cap_requires_relogin(client):
    tokens = signup_and_get_tokens(client)
    too_old = datetime.now(timezone.utc) - timedelta(hours=settings.absolute_session_max_hours, minutes=1)
    _backdate_session_start(tokens["refresh_token"], too_old)

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401

    # The expired-session token is revoked, not just rejected once.
    reuse = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401


def test_refresh_within_absolute_cap_preserves_original_session_start(client):
    tokens = signup_and_get_tokens(client)
    original_start = datetime.now(timezone.utc) - timedelta(hours=1)
    _backdate_session_start(tokens["refresh_token"], original_start)

    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_refresh_token = refreshed.json()["refresh_token"]

    db = TestSessionLocal()
    try:
        new_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == hash_refresh_token(new_refresh_token))
            .one()
        )
        # Rotation must carry the original session_started_at forward, not
        # reset it - otherwise the absolute cap would be a sliding window.
        assert new_token.session_started_at == original_start
    finally:
        db.close()
