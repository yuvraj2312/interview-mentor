from unittest.mock import patch

from app.embedding_adapter import get_embedding_adapter
from app.models import JobDescription, Resume
from app.services import skill_gap_service
from tests.conftest import signup_and_get_tokens

JD_FAKE_ANALYSIS = {
    "required_skills": ["Python", "PostgreSQL"],
    "preferred_skills": ["Docker", "Kubernetes"],
    "seniority_level": "senior",
    "low_confidence_fields": [],
}

# Real adapter, real model - deterministic on CPU, so assertions below are
# reproducible without mocking (matches this repo's no-mocked-infra style).
_embedding_adapter = get_embedding_adapter()


def test_compute_pure_function():
    resume = Resume(structured_data={"skills": ["Python", "FastAPI", "Docker"]})
    jd = JobDescription(
        structured_data={"required_skills": ["Python", "PostgreSQL"], "preferred_skills": ["Docker", "Kubernetes"]}
    )

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert set(result["matched_skills"]) == {"Python", "Docker"}
    assert result["missing_required_skills"] == ["PostgreSQL"]
    assert result["missing_preferred_skills"] == ["Kubernetes"]
    assert result["match_score"] == 0.5


def test_compute_handles_no_requirements():
    resume = Resume(structured_data={"skills": ["Python"]})
    jd = JobDescription(structured_data={"required_skills": [], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["match_score"] == 0.0


def test_compute_matches_js_javascript():
    # Documented Phase 2 limitation (skill_gap_service.py's old docstring):
    # exact-string matching missed this synonym pair. Phase 6a fixes it.
    resume = Resume(structured_data={"skills": ["JS"]})
    jd = JobDescription(structured_data={"required_skills": ["JavaScript"], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["matched_skills"] == ["JavaScript"]
    assert result["missing_required_skills"] == []
    assert result["match_score"] == 1.0


def test_compute_matches_postgres_postgresql():
    resume = Resume(structured_data={"skills": ["Postgres"]})
    jd = JobDescription(structured_data={"required_skills": ["PostgreSQL"], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["matched_skills"] == ["PostgreSQL"]
    assert result["missing_required_skills"] == []
    assert result["match_score"] == 1.0


def test_compute_matches_via_alias_table_not_just_embeddings():
    # "K8s"/"Kubernetes" scores ~0.67 cosine similarity - below the 0.85
    # embedding fallback threshold - so this only passes because of the
    # curated alias table, proving that layer is doing real work.
    resume = Resume(structured_data={"skills": ["K8s"]})
    jd = JobDescription(structured_data={"required_skills": ["Kubernetes"], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["matched_skills"] == ["Kubernetes"]
    assert result["missing_required_skills"] == []


def test_compute_rejects_unrelated_skills():
    # Negative control: proves the similarity threshold doesn't just match
    # everything - an objective guard against a too-loose upgrade.
    resume = Resume(structured_data={"skills": ["Python"]})
    jd = JobDescription(structured_data={"required_skills": ["Kubernetes"], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["Kubernetes"]
    assert result["match_score"] == 0.0


def test_compute_rejects_false_friend_java_javascript():
    # The concrete false-positive risk that ruled out a pure-embedding
    # design: "Java" vs "JavaScript" scores ~0.83 cosine similarity, which
    # would clear a looser threshold despite not being the same skill.
    resume = Resume(structured_data={"skills": ["Java"]})
    jd = JobDescription(structured_data={"required_skills": ["JavaScript"], "preferred_skills": []})

    result = skill_gap_service.compute(resume, jd, _embedding_adapter)

    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JavaScript"]


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
