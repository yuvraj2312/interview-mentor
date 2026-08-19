"""Skill-gap comparison. Deterministic set comparison over already-extracted
skill lists - no LLM call needed since both inputs are already LLM-extracted.

Known limitation (not a bug): matching is exact-string only (case/whitespace
normalized), so synonyms and related skills - e.g. "JS" vs "JavaScript",
"Postgres" vs "PostgreSQL" - won't match. See docs/architecture.md Phase 6
note: once the vector DB is introduced there, this should move to
semantic/embedding-based comparison.
"""

from app.models import JobDescription, Resume


def compute(resume: Resume, jd: JobDescription) -> dict:
    resume_skills = {s.strip().lower() for s in resume.structured_data.get("skills", [])}
    required_skills = jd.structured_data.get("required_skills", [])
    preferred_skills = jd.structured_data.get("preferred_skills", [])

    required_lookup = {s.strip().lower(): s for s in required_skills}
    preferred_lookup = {s.strip().lower(): s for s in preferred_skills}

    matched_required = {s for s in required_lookup if s in resume_skills}
    matched_preferred = {s for s in preferred_lookup if s in resume_skills}

    matched_skills = [required_lookup[s] for s in matched_required] + [
        preferred_lookup[s] for s in matched_preferred
    ]
    missing_required_skills = [required_lookup[s] for s in required_lookup if s not in resume_skills]
    missing_preferred_skills = [preferred_lookup[s] for s in preferred_lookup if s not in resume_skills]

    total = len(required_lookup) + len(preferred_lookup)
    match_score = (len(matched_required) + len(matched_preferred)) / total if total else 0.0

    return {
        "matched_skills": matched_skills,
        "missing_required_skills": missing_required_skills,
        "missing_preferred_skills": missing_preferred_skills,
        "match_score": match_score,
    }
