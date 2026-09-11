import uuid
from unittest.mock import MagicMock, patch

from app.core.security import decode_access_token
from app.repositories import interview_plan_repository
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_plans import _compute_skill_gap, _create_ready_jd, _upload_and_ready_resume

WIDE_PLAN_FAKE_RESULT = {
    "candidate_level": "mid",
    "topic_mix": [
        {"topic": "Python fundamentals", "question_count": 3},
        {"topic": "System design", "question_count": 2},
    ],
    "difficulty_min": 1,
    "difficulty_max": 5,
    "rationale": "Wide range to exercise adaptive difficulty trending.",
}

# CE-a: a plan whose topic_mix already carries the Interview Planner's
# grounded_in_project tagging, for testing that it survives topic_mix ->
# topic_queue -> generate_question end to end (the tagging logic itself is
# unit-tested against the real agent in test_interview_planner_agent.py).
GROUNDED_PLAN_FAKE_RESULT = {
    "candidate_level": "mid",
    "topic_mix": [
        {"topic": "Python fundamentals", "question_count": 2, "grounded_in_project": False, "project": None},
        {
            "topic": "Order Pipeline — project deep-dive",
            "question_count": 1,
            "grounded_in_project": True,
            "project": {
                "name": "Order Pipeline",
                "description": "Async order processing service.",
                "technologies": ["Python", "Kafka"],
            },
        },
        {"topic": "System design", "question_count": 2, "grounded_in_project": False, "project": None},
    ],
    "difficulty_min": 1,
    "difficulty_max": 5,
    "rationale": "Includes one project-grounded slot.",
}


def _ready_plan(client, access_token):
    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])
    with patch("app.services.interview_plan_service.generate_interview_plan", return_value=WIDE_PLAN_FAKE_RESULT):
        response = client.post(
            "/interview-plans",
            json={"skill_gap_analysis_id": skill_gap["id"], "format": "quick"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 201, response.text
    return response.json()


def _fake_generate_question(llm, *, topic, difficulty, candidate_level, asked_questions, project=None):
    return {"question_text": f"Question #{len(asked_questions)} on {topic} (d{difficulty})"}


def _score(value: float) -> dict:
    return {
        "technical_score": value,
        "communication_score": value,
        "completeness_score": value,
        "rationale": "canned",
    }


def _start_session(client, access_token, plan_id):
    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question):
        response = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_interview_sessions_require_auth(client):
    response = client.post(
        "/interview-sessions", json={"interview_plan_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 401


def test_start_session_first_question_at_plan_midpoint(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)

    start = _start_session(client, access_token, plan["id"])

    assert start["total_questions"] == 5
    # round((1 + 5) / 2) == 3
    assert start["question"]["difficulty"] == 3
    assert plan["difficulty_min"] <= start["question"]["difficulty"] <= plan["difficulty_max"]


def test_difficulty_trends_toward_max_with_strong_answers(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    difficulties = [start["question"]["difficulty"]]
    strong_scores = [_score(9.5) for _ in range(5)]
    summary = None

    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=strong_scores
    ):
        for _ in range(5):
            response = client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "A thorough, correct, well-structured answer."},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            if body["status"] == "in_progress":
                difficulties.append(body["next_question"]["difficulty"])
            else:
                summary = body["summary"]

    assert difficulties == sorted(difficulties)  # non-decreasing turn over turn
    assert max(difficulties) == plan["difficulty_max"]
    assert summary["difficulty_path"] == difficulties
    assert all(plan["difficulty_min"] <= d <= plan["difficulty_max"] for d in summary["difficulty_path"])


def test_difficulty_trends_toward_min_with_weak_answers(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    difficulties = [start["question"]["difficulty"]]
    weak_scores = [_score(1.0) for _ in range(5)]

    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=weak_scores
    ):
        for _ in range(5):
            response = client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "uh, I don't know."},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            if body["status"] == "in_progress":
                difficulties.append(body["next_question"]["difficulty"])

    assert difficulties == sorted(difficulties, reverse=True)  # non-increasing turn over turn
    assert min(difficulties) == plan["difficulty_min"]


def test_session_completes_after_question_count_turns_with_summary(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)
    start = _start_session(client, access_token, plan["id"])
    session_id = start["session_id"]

    mid_scores = [_score(6.0) for _ in range(5)]
    last_body = None

    with patch("app.workflows.interview_graph.generate_question", side_effect=_fake_generate_question), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=mid_scores
    ):
        for _ in range(5):
            response = client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "a middling answer"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200, response.text
            last_body = response.json()

    assert last_body["status"] == "complete"
    assert len(last_body["summary"]["difficulty_path"]) == 5
    assert last_body["summary"]["avg_technical_score"] == 6.0

    # session is complete: answering again should now 400
    again = client.post(
        f"/interview-sessions/{session_id}/answer",
        json={"answer_text": "still going?"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert again.status_code == 400

    transcript = client.get(
        f"/interview-sessions/{session_id}", headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    assert transcript["status"] == "complete"
    assert len(transcript["turns"]) == 5
    assert all(turn["evaluation"] is not None for turn in transcript["turns"])


def test_generate_question_receives_growing_asked_questions_list_and_no_duplicates(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    plan = _ready_plan(client, access_token)

    spy = MagicMock(side_effect=_fake_generate_question)
    with patch("app.workflows.interview_graph.generate_question", spy):
        start = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan["id"]},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()
    session_id = start["session_id"]

    scores = [_score(9.5) for _ in range(4)]
    with patch("app.workflows.interview_graph.generate_question", spy), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=scores
    ):
        for _ in range(4):  # the 5th (final) answer completes the session, no further generate_question call
            client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "strong answer"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

    asked_lengths = [len(call.kwargs["asked_questions"]) for call in spy.call_args_list]
    assert asked_lengths == list(range(len(asked_lengths)))  # 0, 1, 2, 3, 4 - strictly growing, no repeats fed back

    # the last (longest) asked_questions list carries every prior question exactly once - no duplicates accrued
    final_asked_questions = spy.call_args_list[-1].kwargs["asked_questions"]
    assert len(final_asked_questions) == len(set(final_asked_questions))


def test_generate_question_receives_project_only_for_the_grounded_slot(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])
    with patch(
        "app.services.interview_plan_service.generate_interview_plan", return_value=GROUNDED_PLAN_FAKE_RESULT
    ):
        plan = client.post(
            "/interview-plans",
            json={"skill_gap_analysis_id": skill_gap["id"], "format": "quick"},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

    spy = MagicMock(side_effect=_fake_generate_question)
    with patch("app.workflows.interview_graph.generate_question", spy):
        start = client.post(
            "/interview-sessions",
            json={"interview_plan_id": plan["id"]},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()
    session_id = start["session_id"]

    scores = [_score(9.5) for _ in range(4)]
    with patch("app.workflows.interview_graph.generate_question", spy), patch(
        "app.workflows.interview_graph.evaluate_answer", side_effect=scores
    ):
        for _ in range(4):
            client.post(
                f"/interview-sessions/{session_id}/answer",
                json={"answer_text": "strong answer"},
                headers={"Authorization": f"Bearer {access_token}"},
            )

    projects_received = [call.kwargs["project"] for call in spy.call_args_list]
    # topic_queue order matches topic_mix order: 2 ungrounded, then the 1
    # grounded slot, then 2 more ungrounded.
    assert projects_received == [None, None, {"name": "Order Pipeline", "description": "Async order processing service.", "technologies": ["Python", "Kafka"]}, None, None]


def test_start_session_requires_ready_plan(client):
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
        plan_id = str(plan.id)
    finally:
        db.close()

    response = client.post(
        "/interview-sessions",
        json={"interview_plan_id": plan_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


def test_user_cannot_start_session_from_another_users_plan(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens_a["access_token"])

    response = client.post(
        "/interview-sessions",
        json={"interview_plan_id": plan["id"]},
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert response.status_code == 404


def test_user_cannot_access_another_users_session(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)
    plan = _ready_plan(client, tokens_a["access_token"])
    start = _start_session(client, tokens_a["access_token"], plan["id"])

    response = client.get(
        f"/interview-sessions/{start['session_id']}", headers={"Authorization": f"Bearer {tokens_b['access_token']}"}
    )
    assert response.status_code == 404
