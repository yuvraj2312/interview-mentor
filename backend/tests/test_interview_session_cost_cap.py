"""Phase 4d per-session cost cap.

Deliberately does NOT reuse the rest of this suite's pattern of patching
app.workflows.interview_graph.generate_question/evaluate_answer directly -
that bypasses llm.generate() entirely, so llm.last_usage (what the cap
reads) would never be set. Instead these tests patch
app.services.interview_session_service.get_llm_adapter with a
FakeLLMAdapter (tests/fakes.py) that lets the real agent functions run
against scripted, zero-network responses with a controllable per-call cost
- deterministic, no real tokens burned, and exercises the real parsing
code path.
"""

import json
from unittest.mock import patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from tests.conftest import signup_and_get_tokens
from tests.fakes import fake_llm_factory
from tests.test_interview_sessions import _ready_plan


def _question_response(text: str) -> str:
    return json.dumps({"question_text": text})


def _evaluation_response(score: float = 6.0) -> str:
    return json.dumps(
        {
            "technical_score": score,
            "communication_score": score,
            "completeness_score": score,
            "rationale": "canned",
        }
    )


def _start_with_fake_llm(client, access_token, plan_id, factory):
    with patch("app.services.interview_session_service.get_llm_adapter", side_effect=factory):
        response = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_session_stops_early_when_cost_cap_exceeded(client, monkeypatch):
    monkeypatch.setattr(settings, "interview_session_max_cost_usd", 3.0)

    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)

    responses = [_question_response("Q0")]
    factory = fake_llm_factory(responses, cost_per_call=2.0)

    start = _start_with_fake_llm(client, access_token, plan["id"], factory)
    session_id = start["session_id"]
    assert start["total_questions"] == 5  # cap must trip well before natural completion

    # evaluate_answer ($2) pushes accumulated cost from $2 -> $4, over the
    # $3 cap: the loop must stop here, not generate a next question.
    responses.append(_evaluation_response())
    with patch("app.services.interview_session_service.get_llm_adapter", side_effect=factory):
        response = client.post(
            f"/interview-sessions/{session_id}/answer",
            json={"answer_text": "an answer"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "complete"
    assert body["stop_reason"] == "cost_cap_exceeded"
    assert body["total_cost_usd"] == 4.0
    assert body["cost_cap_usd"] == 3.0
    assert responses == []  # no next-question call was made after the cap tripped

    state_response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert state_response.status_code == 200, state_response.text
    state_body = state_response.json()
    assert state_body["status"] == "complete"
    assert state_body["stop_reason"] == "cost_cap_exceeded"
    assert state_body["total_cost_usd"] == 4.0

    # already-complete: answering again still 400s, same as natural completion
    again = client.post(
        f"/interview-sessions/{session_id}/answer",
        json={"answer_text": "still going?"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert again.status_code == 400


def test_running_cost_persists_across_turns_below_cap(client, monkeypatch):
    monkeypatch.setattr(settings, "interview_session_max_cost_usd", 100.0)

    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)

    responses = [_question_response("Q0")]
    factory = fake_llm_factory(responses, cost_per_call=0.1)

    start = _start_with_fake_llm(client, access_token, plan["id"], factory)
    session_id = start["session_id"]

    responses.extend([_evaluation_response(), _question_response("Q1")])
    with patch("app.services.interview_session_service.get_llm_adapter", side_effect=factory):
        response = client.post(
            f"/interview-sessions/{session_id}/answer",
            json={"answer_text": "an answer"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["stop_reason"] is None
    # start (0.1) + evaluate (0.1) + next question (0.1)
    assert round(body["total_cost_usd"], 2) == 0.30

    # A reconnect / GET state must reflect the running total, not reset it.
    state_response = client.get(
        f"/interview-sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert round(state_response.json()["total_cost_usd"], 2) == 0.30


def test_ws_session_stops_early_on_cost_cap(client, monkeypatch):
    monkeypatch.setattr(settings, "interview_session_max_cost_usd", 3.0)

    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)

    responses = [_question_response("Q0")]
    factory = fake_llm_factory(responses, cost_per_call=2.0)

    start = _start_with_fake_llm(client, access_token, plan["id"], factory)
    session_id = start["session_id"]

    responses.append(_evaluation_response())
    with client.websocket_connect(f"/ws/interview-sessions/{session_id}") as connection:
        connection.send_json({"type": "auth", "token": access_token})
        connection.receive_json()  # initial state

        with patch("app.services.interview_session_service.get_llm_adapter", side_effect=factory):
            connection.send_json({"type": "answer", "answer_text": "an answer"})
            result = connection.receive_json()

        assert result["status"] == "complete"
        assert result["stop_reason"] == "cost_cap_exceeded"
        assert result["total_cost_usd"] == 4.0

        with pytest.raises(WebSocketDisconnect) as exc_info:
            connection.receive_json()
    assert exc_info.value.code == 1000
