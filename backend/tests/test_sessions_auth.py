from unittest.mock import patch

from tests.conftest import signup_and_get_tokens

FAKE_QUESTIONS = [
    {"topic": "Python", "difficulty": "easy", "question": "What is a list comprehension?"},
    {"topic": "SQL", "difficulty": "medium", "question": "What is a JOIN?"},
    {"topic": "Testing", "difficulty": "hard", "question": "How do you mock a dependency?"},
]


def _start_session(client, access_token):
    with patch("app.services.interview_service.generate_questions", return_value=FAKE_QUESTIONS):
        return client.post(
            "/sessions",
            json={"resume_text": "resume", "jd_text": "jd"},
            headers={"Authorization": f"Bearer {access_token}"},
        )


def test_create_session_requires_auth(client):
    response = client.post("/sessions", json={"resume_text": "resume", "jd_text": "jd"})
    assert response.status_code == 401


def test_create_session_sets_owner(client):
    tokens = signup_and_get_tokens(client)
    response = _start_session(client, tokens["access_token"])
    assert response.status_code == 200
    assert response.json()["question"]["text"] == FAKE_QUESTIONS[0]["question"]


def test_user_cannot_access_another_users_session(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)

    created = _start_session(client, tokens_a["access_token"])
    session_id = created.json()["session_id"]

    response = client.get(
        f"/sessions/{session_id}",
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert response.status_code == 404

    answer_response = client.post(
        f"/sessions/{session_id}/answer",
        json={"answer_text": "some answer"},
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert answer_response.status_code == 404
