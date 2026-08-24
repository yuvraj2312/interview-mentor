import uuid
from unittest.mock import patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.repositories import interview_session_state_repository as state_repo
from tests.conftest import signup_and_get_tokens
from tests.test_interview_sessions import _fake_generate_question, _ready_plan, _score

WS_PATH = "/ws/interview-sessions/{session_id}"


def _create_session(client, access_token, plan_id):
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question):
        response = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_ws_receives_initial_state_and_question(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        message = connection.receive_json()

    assert message["type"] == "state"
    assert message["session_id"] == start["session_id"]
    assert message["interview_plan_id"] == plan["id"]
    assert message["status"] == "in_progress"
    assert message["turn_index"] == 0
    assert message["current_question"] == start["question"]
    assert message["summary"] is None


def test_ws_closes_4401_without_auth_message(client, monkeypatch):
    monkeypatch.setattr(settings, "ws_auth_timeout_seconds", 0.05)
    tokens = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens["access_token"])
    start = _create_session(client, tokens["access_token"], plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 4401


def test_ws_closes_4401_with_invalid_token(client):
    tokens = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens["access_token"])
    start = _create_session(client, tokens["access_token"], plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        connection.send_json({"type": "auth", "token": "not-a-real-token"})
        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 4401


def test_ws_closes_4404_for_session_not_owned(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens_a["access_token"])
    start = _create_session(client, tokens_a["access_token"], plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        connection.send_json({"type": "auth", "token": tokens_b["access_token"]})
        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 4404


def test_ws_submit_answer_returns_evaluation_and_next_question(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        connection.receive_json()  # initial state
        with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
            "app.workflows.interview_graph.evaluate_answer", return_value=_score(6.0)
        ):
            connection.send_json({"type": "answer", "answer_text": "a middling answer"})
            result = connection.receive_json()

    assert result["type"] == "answer_result"
    assert result["status"] == "in_progress"
    assert result["evaluation"]["technical_score"] == 6.0
    assert result["next_question"]["turn_index"] == 1
    assert result["summary"] is None


def test_ws_session_completes_and_closes(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])

    with client.websocket_connect(WS_PATH.format(session_id=start["session_id"])) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        connection.receive_json()  # initial state
        last_result = None
        for _ in range(5):
            with patch(
                "app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question
            ), patch("app.workflows.interview_graph.evaluate_answer", return_value=_score(6.0)):
                connection.send_json({"type": "answer", "answer_text": "a middling answer"})
                last_result = connection.receive_json()

        assert last_result["status"] == "complete"
        assert last_result["summary"]["difficulty_path"] == [3, 3, 3, 3, 3]

        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 1000


def test_ws_reconnect_resumes_after_close(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    with client.websocket_connect(WS_PATH.format(session_id=session_id)) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        connection.receive_json()
        with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
            "app.workflows.interview_graph.evaluate_answer", return_value=_score(6.0)
        ):
            connection.send_json({"type": "answer", "answer_text": "a middling answer"})
            connection.receive_json()
    # connection closed here, simulating a dropped tab

    with client.websocket_connect(WS_PATH.format(session_id=session_id)) as connection2:
        connection2.send_json({"type": "auth", "token": access_token})
        message = connection2.receive_json()

    assert message["status"] == "in_progress"
    assert message["turn_index"] == 1
    assert message["current_question"]["turn_index"] == 1


def test_ws_reconnect_after_redis_loss(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    with client.websocket_connect(WS_PATH.format(session_id=session_id)) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        connection.receive_json()
        with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
            "app.workflows.interview_graph.evaluate_answer", return_value=_score(6.0)
        ):
            connection.send_json({"type": "answer", "answer_text": "a middling answer"})
            connection.receive_json()

    state_repo.delete(uuid.UUID(session_id))
    assert state_repo.load(uuid.UUID(session_id)) is None

    with client.websocket_connect(WS_PATH.format(session_id=session_id)) as connection2:
        connection2.send_json({"type": "auth", "token": access_token})
        message = connection2.receive_json()

    assert message["status"] == "in_progress"
    assert message["turn_index"] == 1
    assert state_repo.load(uuid.UUID(session_id)) is not None


def test_ws_reports_abandoned_on_reconnect_after_inactivity_gap(client, monkeypatch):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _create_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    monkeypatch.setattr(settings, "interview_session_inactivity_timeout_seconds", -1)

    with client.websocket_connect(WS_PATH.format(session_id=session_id)) as connection:
        connection.send_json({"type": "auth", "token": access_token})
        message = connection.receive_json()
        assert message["status"] == "abandoned"

        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 1000
