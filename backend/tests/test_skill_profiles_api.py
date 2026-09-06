from unittest.mock import patch

from tests.conftest import signup_and_get_tokens
from tests.test_interview_sessions import _fake_generate_question, _ready_plan, _score
from tests.test_skill_profile_service import _BASE_TIME, _recompute, _seed_completed_session, _setup_user_and_plan


def test_get_skill_profile_404_when_no_sessions(client):
    tokens = signup_and_get_tokens(client)
    response = client.get("/skill-profile", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 404


def test_get_skill_profile_returns_seeded_data(client):
    access_token, user_id, plan_id = _setup_user_and_plan(client)
    _seed_completed_session(
        user_id, plan_id, [("Python", 8.0, 6.0, 7.0), ("System Design", 4.0, 4.0, 4.0)], completed_at=_BASE_TIME
    )
    _recompute(user_id)

    response = client.get("/skill-profile", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["sessions_completed"] == 1
    assert body["overall_avg_technical_score"] == 6.0
    topics = {t["topic"]: t for t in body["topics"]}
    assert set(topics) == {"Python", "System Design"}
    assert topics["Python"]["trend"] == "insufficient_data"


def test_get_skill_profile_reflects_completed_session_via_real_flow(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question):
        start = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan["id"]},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()
    session_id = start["session_id"]

    mid_scores = [_score(6.0) for _ in range(5)]
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=mid_scores
    ):
        last_body = None
        for _ in range(5):
            response = client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "a middling answer"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200, response.text
            last_body = response.json()
    assert last_body["status"] == "complete"

    profile_response = client.get("/skill-profile", headers={"Authorization": f"Bearer {access_token}"})
    assert profile_response.status_code == 200, profile_response.text
    body = profile_response.json()

    assert body["sessions_completed"] == 1
    assert body["overall_avg_technical_score"] == 6.0
    assert body["overall_avg_communication_score"] == 6.0
    assert body["overall_avg_completeness_score"] == 6.0
    topics = {t["topic"] for t in body["topics"]}
    assert topics == {"Python fundamentals", "System design"}
    for t in body["topics"]:
        assert t["trend"] == "insufficient_data"
