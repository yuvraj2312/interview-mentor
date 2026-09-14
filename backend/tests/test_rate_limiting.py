from tests.conftest import unique_email


def test_login_rate_limit_triggers_on_rapid_repeated_requests(client):
    email = unique_email()
    client.post("/auth/signup", json={"email": email, "password": "correct-horse"})

    statuses = [
        client.post("/auth/login", json={"email": email, "password": "wrong-password"}).status_code
        for _ in range(15)
    ]

    assert 429 in statuses
    # The limit only kicks in after the configured number of attempts, not
    # on the first request - confirms this isn't blocking normal use.
    assert statuses[0] != 429


def test_signup_rate_limit_triggers_on_rapid_repeated_requests(client):
    statuses = [
        client.post("/auth/signup", json={"email": unique_email(), "password": "correct-horse"}).status_code
        for _ in range(10)
    ]

    assert 429 in statuses
    assert statuses[0] == 201
