"""Skill-gap comparison: exact-string match, then curated-alias match, then
embedding cosine similarity for anything still unmatched, over already-
extracted skill lists - no LLM call needed since both inputs are already
LLM-extracted.

The exact pass alone used to miss synonyms and related skills (e.g. "JS" vs
"JavaScript", "Postgres" vs "PostgreSQL"). Cosine similarity on bare skill
tokens can't safely resolve those alone either - it can't separate true
synonyms from false friends like "Java"/"JavaScript" (see skill_aliases.py
docstring for the data) - so well-known cases are resolved deterministically
via SKILL_ALIASES first, and embeddings are a conservative fallback for
whatever's left. This function's output shape is unchanged from Phase 2.
"""

from math import sqrt

from app.core.config import settings
from app.core.skill_aliases import canonicalize
from app.embedding_adapter import EmbeddingAdapter
from app.models import JobDescription, Resume


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _semantic_match(
    jd_norms: list[str],
    jd_lookup: dict[str, str],
    resume_lookup: dict[str, str],
    embedding_adapter: EmbeddingAdapter,
) -> set[str]:
    if not jd_norms or not resume_lookup:
        return set()

    resume_norms = list(resume_lookup)
    jd_vectors = embedding_adapter.embed([jd_lookup[n] for n in jd_norms])
    resume_vectors = embedding_adapter.embed([resume_lookup[n] for n in resume_norms])

    matched = set()
    for norm, vector in zip(jd_norms, jd_vectors):
        best = max((_cosine_similarity(vector, rv) for rv in resume_vectors), default=0.0)
        if best >= settings.skill_match_similarity_threshold:
            matched.add(norm)
    return matched


def compute(resume: Resume, jd: JobDescription, embedding_adapter: EmbeddingAdapter) -> dict:
    resume_lookup = {s.strip().lower(): s for s in resume.structured_data.get("skills", [])}
    required_lookup = {s.strip().lower(): s for s in jd.structured_data.get("required_skills", [])}
    preferred_lookup = {s.strip().lower(): s for s in jd.structured_data.get("preferred_skills", [])}

    resume_canonical = {canonicalize(n) for n in resume_lookup}
    all_jd_norms = set(required_lookup) | set(preferred_lookup)
    exact_matched = {n for n in all_jd_norms if canonicalize(n) in resume_canonical}
    unmatched_norms = [n for n in all_jd_norms if n not in exact_matched]
    jd_text_lookup = {**required_lookup, **preferred_lookup}
    semantic_matched = _semantic_match(unmatched_norms, jd_text_lookup, resume_lookup, embedding_adapter)
    matched_norms = exact_matched | semantic_matched

    matched_required = {s for s in required_lookup if s in matched_norms}
    matched_preferred = {s for s in preferred_lookup if s in matched_norms}

    matched_skills = [required_lookup[s] for s in matched_required] + [
        preferred_lookup[s] for s in matched_preferred
    ]
    missing_required_skills = [required_lookup[s] for s in required_lookup if s not in matched_norms]
    missing_preferred_skills = [preferred_lookup[s] for s in preferred_lookup if s not in matched_norms]

    total = len(required_lookup) + len(preferred_lookup)
    match_score = (len(matched_required) + len(matched_preferred)) / total if total else 0.0

    return {
        "matched_skills": matched_skills,
        "missing_required_skills": missing_required_skills,
        "missing_preferred_skills": missing_preferred_skills,
        "match_score": match_score,
    }
