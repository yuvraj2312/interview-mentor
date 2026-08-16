from tests.conftest import signup_and_get_tokens, unique_email


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
