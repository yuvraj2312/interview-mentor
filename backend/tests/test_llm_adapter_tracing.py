import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.core.security import decode_access_token
from app.llm_adapter import AnthropicAdapter
from app.models import LLMCall
from app.repositories import interview_plan_repository, interview_session_repository
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_plans import _compute_skill_gap, _create_ready_jd, _upload_and_ready_resume


def _fake_response(text="hello", input_tokens=12, output_tokens=34):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def test_generate_persists_trace_row_with_usage_and_cost():
    db = TestSessionLocal()
    try:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _fake_response()
        with patch("app.llm_adapter.anthropic.Anthropic", return_value=mock_client):
            adapter = AnthropicAdapter(db, session_id=None)
            text = adapter.generate("a prompt", agent_name="resume_analyzer", temperature=0.2, max_tokens=100)
        db.commit()

        assert text == "hello"
        assert adapter.last_usage is not None
        assert adapter.last_usage.input_tokens == 12
        assert adapter.last_usage.output_tokens == 34
        assert adapter.last_usage.cost_usd > 0

        row = db.query(LLMCall).one()
        assert row.agent_name == "resume_analyzer"
        assert row.session_id is None
        assert row.model
        assert row.status == "success"
        assert row.input_tokens == 12
        assert row.output_tokens == 34
        assert row.prompt == "a prompt"
        assert row.response == "hello"
        assert row.temperature == 0.2
        assert row.max_tokens == 100
        assert row.latency_ms >= 0
        assert row.cost_usd == pytest.approx(adapter.last_usage.cost_usd)
        assert row.error_message is None
    finally:
        db.close()


def test_generate_persists_error_row_and_reraises():
    db = TestSessionLocal()
    try:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("boom")
        with patch("app.llm_adapter.anthropic.Anthropic", return_value=mock_client):
            adapter = AnthropicAdapter(db, session_id=None)
            with pytest.raises(RuntimeError):
                adapter.generate("a prompt", agent_name="evaluator")
        db.commit()

        assert adapter.last_usage is None
        row = db.query(LLMCall).one()
        assert row.status == "error"
        assert row.error_message == "boom"
        assert row.input_tokens is None
        assert row.output_tokens is None
        assert row.cost_usd is None
        assert row.latency_ms >= 0
    finally:
        db.close()


def test_generate_tags_trace_row_with_session_id(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    user_id = uuid.UUID(decode_access_token(access_token)["sub"])

    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])

    db = TestSessionLocal()
    try:
        plan = interview_plan_repository.create(
            db,
            user_id=user_id,
            resume_id=uuid.UUID(resume_id),
            job_description_id=uuid.UUID(jd["id"]),
            skill_gap_analysis_id=uuid.UUID(skill_gap["id"]),
            format="quick",
        )
        db.commit()

        session = interview_session_repository.create(
            db,
            user_id=user_id,
            interview_plan_id=plan.id,
            total_questions=1,
            current_difficulty=1,
            topic_queue=[],
            asked_questions=[],
            cost_cap_usd=1.0,
        )
        db.commit()

        mock_client = MagicMock()
        mock_client.messages.create.return_value = _fake_response()
        with patch("app.llm_adapter.anthropic.Anthropic", return_value=mock_client):
            adapter = AnthropicAdapter(db, session_id=session.id)
            adapter.generate("a prompt", agent_name="question_generator")
        db.commit()

        row = db.query(LLMCall).filter(LLMCall.session_id == session.id).one()
        assert row.agent_name == "question_generator"
    finally:
        db.close()
