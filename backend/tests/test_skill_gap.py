from unittest.mock import patch

from app.models import JobDescription, Resume
from app.services import skill_gap_service
from tests.conftest import signup_and_get_tokens

JD_FAKE_ANALYSIS = {
    "required_skills": ["Python", "PostgreSQL"],
    "preferred_skills": ["Docker", "Kubernetes"],
    "seniority_level": "senior",
    "low_confidence_fields": [],
}


def test_compute_pure_function():
    resume = Resume(structured_data={"skills": ["Python", "FastAPI", "Docker"]})
    jd = JobDescription(
        structured_data={"required_skills": ["Python", "PostgreSQL"], "preferred_skills": ["Docker", "Kubernetes"]}
    )

    result = skill_gap_service.compute(resume, jd)

    assert set(result["matched_skills"]) == {"Python", "Docker"}
    assert result["missing_required_skills"] == ["PostgreSQL"]
    assert result["missing_preferred_skills"] == ["Kubernetes"]
    assert result["match_score"] == 0.5


def test_compute_handles_no_requirements():
    resume = Resume(structured_data={"skills": ["Python"]})
    jd = JobDescription(structured_data={"required_skills": [], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd)

    assert result["match_score"] == 0.0


def _upload_resume(client, access_token):
    import io

    from docx import Document

    doc = Document()
    doc.add_paragraph("Candidate")
    buf = io.BytesIO()
    doc.save(buf)

    upload_response = client.post(
        "/resumes",
        files={
            "file": (
                "resume.docx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return upload_response.json()


def test_skill_gap_requires_ready_resume(client):
    # No Arq worker runs during tests, so the uploaded resume stays in
    # "uploaded" status (never reaches "ready") - this exercises the
    # not-ready guard on POST /skill-gap.
    tokens = signup_and_get_tokens(client)
    uploaded = _upload_resume(client, tokens["access_token"])

    with patch("app.services.job_description_service.analyze_job_description", return_value=JD_FAKE_ANALYSIS):
        jd = client.post(
            "/job-descriptions",
            json={"raw_text": "some jd"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        ).json()

    response = client.post(
        "/skill-gap",
        json={"resume_id": uploaded["id"], "job_description_id": jd["id"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 400
