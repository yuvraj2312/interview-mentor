import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.core.config import settings
from app.core.security import decode_access_token
from app.repositories import interview_session_repository, interview_session_state_repository as state_repo
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_sessions import (
    _fake_generate_question,
    _ready_plan,
    _score,
    _start_session,
)


def _answer_turn(client, access_token, session_id, score_value=6.0):
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", return_value=_score(score_value)
    ):
        response = client.post(
            f"/interview-sessions/{session_id}/answer",
            json={"answer_text": "a middling answer"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_get_state_reports_in_progress_with_current_question(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])

    response = client.get(
        f"/interview-sessions/{start['session_id']}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "in_progress"
    assert body["turn_index"] == 0
    assert body["total_questions"] == start["total_questions"]
    assert body["current_difficulty"] == start["question"]["difficulty"]
    assert body["current_question"] == start["question"]


def test_state_survives_redis_key_loss_and_repopulates_from_postgres(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    _answer_turn(client, access_token, session_id)

    state_repo.delete(uuid.UUID(session_id))
    assert state_repo.load(uuid.UUID(session_id)) is None

    response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["turn_index"] == 1
    assert body["current_question"]["turn_index"] == 1

    # GET /state repopulated Redis.
    assert state_repo.load(uuid.UUID(session_id)) is not None


def test_submit_answer_recovers_after_redis_key_loss(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    _answer_turn(client, access_token, session_id)

    state_repo.delete(uuid.UUID(session_id))

    body = _answer_turn(client, access_token, session_id)
    assert body["status"] == "in_progress"
    assert body["next_question"]["turn_index"] == 2


def test_inactivity_flips_session_to_abandoned_via_get_state(client, monkeypatch):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    monkeypatch.setattr(settings, "interview_session_inactivity_timeout_seconds", -1)

    response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "abandoned"

    user_id = uuid.UUID(decode_access_token(access_token)["sub"])
    db = TestSessionLocal()
    try:
        session = interview_session_repository.get_by_id_for_user(db, uuid.UUID(session_id), user_id)
        assert session.status == "abandoned"
    finally:
        db.close()

    assert state_repo.load(uuid.UUID(session_id)) is None


def test_submit_answer_returns_409_after_abandonment(client, monkeypatch):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    monkeypatch.setattr(settings, "interview_session_inactivity_timeout_seconds", -1)

    response = client.post(
        f"/interview-sessions/{session_id}/answer",
        json={"answer_text": "too late"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 409


def test_stuck_evaluating_marker_is_discarded_on_read(client, monkeypatch):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    live_state = state_repo.load(uuid.UUID(session_id))
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    state_repo.save({**live_state, "status": "evaluating", "last_activity_at": stale_timestamp})

    monkeypatch.setattr(settings, "interview_session_stuck_transient_seconds", -1)

    response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["current_question"] == start["question"]


def test_postgres_terminal_status_wins_over_stale_redis_hit(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    for _ in range(5):
        body = _answer_turn(client, access_token, session_id)
    assert body["status"] == "complete"
    assert state_repo.load(uuid.UUID(session_id)) is None

    stale_blob = {
        "session_id": session_id,
        "status": "in_progress",
        "turn_index": 4,
        "total_questions": start["total_questions"],
        "current_difficulty": 3,
        "topic_queue": [],
        "asked_questions": [],
        "current_question": None,
        "last_activity_at": datetime.now(timezone.utc).isoformat(),
    }
    state_repo.save(stale_blob)

    response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "complete"

    assert state_repo.load(uuid.UUID(session_id)) is None
