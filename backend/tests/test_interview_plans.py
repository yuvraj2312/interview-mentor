import io
import uuid
from unittest.mock import patch

from docx import Document

from app.agents.interview_planner import clamp_difficulty
from app.repositories import resume_repository
from app.services import resume_service
from tests.conftest import TestSessionLocal, signup_and_get_tokens

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

JD_FAKE_ANALYSIS = {
    "required_skills": ["Python", "PostgreSQL"],
    "preferred_skills": ["Docker"],
    "seniority_level": "senior",
    "low_confidence_fields": [],
}

RESUME_FAKE_ANALYSIS = {
    "skills": ["Python", "FastAPI"],
    "experience": [],
    "education": [],
    "projects": [],
    "low_confidence_fields": [],
}

PLAN_FAKE_RESULT = {
    "candidate_level": "mid",
    "topic_mix": [
        {"topic": "Python fundamentals", "question_count": 3},
        {"topic": "PostgreSQL", "question_count": 2},
    ],
    "difficulty_min": 2,
    "difficulty_max": 3,
    "rationale": "Focused on missing required skills given a mid-level resume.",
}


def _upload_and_ready_resume(client, access_token):
    doc = Document()
    doc.add_paragraph("Candidate")
    buf = io.BytesIO()
    doc.save(buf)

    uploaded = client.post(
        "/resumes",
        files={"file": ("resume.docx", buf.getvalue(), DOCX_CONTENT_TYPE)},
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    db = TestSessionLocal()
    try:
        with patch("app.services.resume_service.analyze_resume", return_value=RESUME_FAKE_ANALYSIS):
            resume_service.process_uploaded_resume(db, uuid.UUID(uploaded["id"]))
    finally:
        db.close()

    return uploaded["id"]


def _create_ready_jd(client, access_token):
    with patch("app.services.job_description_service.analyze_job_description", return_value=JD_FAKE_ANALYSIS):
        return client.post(
            "/job-descriptions",
            json={"raw_text": "We need a senior Python engineer with PostgreSQL experience."},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()


def _compute_skill_gap(client, access_token, resume_id, jd_id):
    return client.post(
        "/skill-gap",
        json={"resume_id": resume_id, "job_description_id": jd_id},
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()


def _set_resume_status(resume_id, status):
    db = TestSessionLocal()
    try:
        resume = resume_repository.get_by_id(db, uuid.UUID(resume_id))
        resume_repository.update_status(db, resume, status=status)
        db.commit()
    finally:
        db.close()


def test_create_interview_plan_requires_auth(client):
    response = client.post("/interview-plans", json={"skill_gap_analysis_id": "00000000-0000-0000-0000-000000000000", "format": "quick"})
    assert response.status_code == 401


def test_create_interview_plan_happy_path(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])

    with patch("app.services.interview_plan_service.generate_interview_plan", return_value=PLAN_FAKE_RESULT):
        response = client.post(
            "/interview-plans",
            json={"skill_gap_analysis_id": skill_gap["id"], "format": "quick"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["question_count"] == 5
    assert body["candidate_level"] == "mid"
    assert body["difficulty_min"] == 2
    assert body["difficulty_max"] == 3
    assert body["resume_id"] == resume_id
    assert body["job_description_id"] == jd["id"]
    assert body["skill_gap_analysis_id"] == skill_gap["id"]

    get_response = client.get(f"/interview-plans/{body['id']}", headers={"Authorization": f"Bearer {access_token}"})
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ready"


def test_create_interview_plan_returns_502_on_malformed_llm_output(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])

    with patch("app.services.interview_plan_service.generate_interview_plan", side_effect=ValueError("malformed")):
        response = client.post(
            "/interview-plans",
            json={"skill_gap_analysis_id": skill_gap["id"], "format": "standard"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 502


def test_create_interview_plan_requires_ready_resume(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    resume_id = _upload_and_ready_resume(client, access_token)
    jd = _create_ready_jd(client, access_token)
    skill_gap = _compute_skill_gap(client, access_token, resume_id, jd["id"])

    # Simulate the resume becoming unusable after the skill gap was already computed.
    _set_resume_status(resume_id, "failed")

    response = client.post(
        "/interview-plans",
        json={"skill_gap_analysis_id": skill_gap["id"], "format": "quick"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


def test_user_cannot_create_plan_from_another_users_skill_gap(client):
    tokens_a = signup_and_get_tokens(client)
    tokens_b = signup_and_get_tokens(client)

    resume_id = _upload_and_ready_resume(client, tokens_a["access_token"])
    jd = _create_ready_jd(client, tokens_a["access_token"])
    skill_gap = _compute_skill_gap(client, tokens_a["access_token"], resume_id, jd["id"])

    response = client.post(
        "/interview-plans",
        json={"skill_gap_analysis_id": skill_gap["id"], "format": "quick"},
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert response.status_code == 404


def test_clamp_difficulty_bounds_junior_below_senior_jd_expectations():
    difficulty_min, difficulty_max = clamp_difficulty("junior", 3, 5)
    assert difficulty_max == 3
    assert difficulty_min == 3


def test_clamp_difficulty_respects_a_valid_in_range_proposal():
    assert clamp_difficulty("senior", 2, 4) == (2, 4)


def test_clamp_difficulty_unknown_level_falls_back_to_default_ceiling():
    difficulty_min, difficulty_max = clamp_difficulty("unknown", 1, 5)
    assert difficulty_max == 4
