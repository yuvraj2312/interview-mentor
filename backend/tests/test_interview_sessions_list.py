from unittest.mock import patch

from tests.conftest import signup_and_get_tokens
from tests.test_interview_sessions import _fake_generate_question, _ready_plan, _score, _start_session


def test_list_sessions_empty_for_new_user(client):
    tokens = signup_and_get_tokens(client)
    response = client.get("/interview-sessions", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_requires_auth(client):
    response = client.get("/interview-sessions")
    assert response.status_code == 401


def test_list_sessions_excludes_other_users_sessions(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens_a["access_token"])
    _start_session(client, tokens_a["access_token"], plan["id"])

    response = client.get("/interview-sessions", headers={"Authorization": f"Bearer {tokens_b['access_token']}"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_null_scores_before_any_answer(client):
    tokens = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens["access_token"])
    start = _start_session(client, tokens["access_token"], plan["id"])

    response = client.get("/interview-sessions", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["session_id"] == start["session_id"]
    assert item["status"] == "in_progress"
    assert item["turns_completed"] == 0
    assert item["avg_technical_score"] is None
    assert item["avg_communication_score"] is None
    assert item["avg_completeness_score"] is None
    assert item["completed_at"] is None


def test_list_sessions_ordered_newest_first_with_averaged_scores(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]

    plan_1 = _ready_plan(client, access_token)
    start_1 = _start_session(client, access_token, plan_1["id"])
    plan_2 = _ready_plan(client, access_token)
    start_2 = _start_session(client, access_token, plan_2["id"])

    scores = [_score(8.0), _score(6.0)]
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=scores
    ):
        client.post(
            f"/interview-sessions/{start_2['session_id']}/answer",
            json={"answer_text": "answer one"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        client.post(
            f"/interview-sessions/{start_2['session_id']}/answer",
            json={"answer_text": "answer two"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    response = client.get("/interview-sessions", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    # newest (most recently created) session first
    assert body[0]["session_id"] == start_2["session_id"]
    assert body[0]["turns_completed"] == 2
    assert body[0]["avg_technical_score"] == 7.0
    assert body[1]["session_id"] == start_1["session_id"]
