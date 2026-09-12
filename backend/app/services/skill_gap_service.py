"""Skill-gap comparison: exact-string match, then curated-alias match, then
embedding cosine similarity, then an LLM fallback for whatever's still
ambiguous, over already-extracted skill lists.

The exact pass alone used to miss synonyms and related skills (e.g. "JS" vs
"JavaScript", "Postgres" vs "PostgreSQL"). Cosine similarity on bare skill
tokens can't safely resolve those alone either - it can't separate true
synonyms from false friends like "Java"/"JavaScript" (see skill_aliases.py
docstring for the data) - so well-known cases are resolved deterministically
via SKILL_ALIASES first, and embeddings are a conservative fallback for
whatever's left.

Layer 4 (LLM fallback, see _llm_fallback_pass) exists because the alias
table only has curated tech entries: outside tech (finance, healthcare, law,
...) there's no alias backstop, and calibration found embedding similarity
below the confident-match threshold is not reliably separable from noise for
short professional-skill phrases - so anything not confidently matched by
embeddings alone gets a small, targeted LLM judgment call instead of being
silently dropped. This function's output shape is unchanged from Phase 2.
"""

from math import sqrt

from app.agents.skill_matcher import llm_fallback_match
from app.core.config import settings
from app.core.skill_aliases import canonicalize
from app.embedding_adapter import EmbeddingAdapter
from app.llm_adapter import LLMAdapter
from app.models import JobDescription, Resume


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Cap on how many above-floor resume candidates get an LLM look per
# unmatched JD skill. Calibration found cosine similarity in the ambiguous
# band is not a reliable ranking signal (a narrowly-lower-scoring true
# synonym can rank behind an unrelated distractor - see the 2026-09-12
# investigation: "Investment Analysis" narrowly outscored "Critical
# Thinking" against JD skill "Analytical skills", 0.713 vs 0.681, and the
# true match was never checked when only the single best candidate was
# sent). Checking only the top candidate let real matches go unnoticed.
# Uncapped ("every candidate above the floor") was rejected: the floor is
# set low enough (see config.py) that nearly every resume skill clears it,
# so an uncapped design could mean one LLM call per resume skill per
# unmatched JD skill - potentially hundreds of calls and minutes of added
# latency for a single skill-gap computation. Top-3 is a bounded
# compromise that already covers every case found during that
# investigation (the true match ranked 2nd or 3rd in each case).
AMBIGUOUS_CANDIDATES_PER_JD_SKILL = 3


def _semantic_match(
    jd_norms: list[str],
    jd_lookup: dict[str, str],
    resume_lookup: dict[str, str],
    embedding_adapter: EmbeddingAdapter,
) -> tuple[set[str], dict[str, list[str]]]:
    """Returns (confidently_matched_norms, ambiguous_candidates), where
    ambiguous_candidates maps a JD norm to up to
    AMBIGUOUS_CANDIDATES_PER_JD_SKILL resume skill texts (original-cased),
    ordered by descending cosine score, for JD norms whose best score
    didn't clear the confident-match threshold. Every one of these
    candidates gets a chance at the LLM fallback - not just the single
    best-scoring one - since a narrowly-higher-scoring distractor must not
    be able to starve a better, lower-scoring true match from ever being
    checked (cosine similarity below the threshold is not a trustworthy
    enough ranking signal to bet everything on the single top pick).
    """
    if not jd_norms or not resume_lookup:
        return set(), {}

    resume_norms = list(resume_lookup)
    jd_vectors = embedding_adapter.embed([jd_lookup[n] for n in jd_norms])
    resume_vectors = embedding_adapter.embed([resume_lookup[n] for n in resume_norms])

    matched: set[str] = set()
    ambiguous_candidates: dict[str, list[str]] = {}
    for norm, vector in zip(jd_norms, jd_vectors):
        scored = [
            (_cosine_similarity(vector, resume_vector), resume_norm)
            for resume_norm, resume_vector in zip(resume_norms, resume_vectors)
        ]
        best_score = max((score for score, _ in scored), default=0.0)
        if best_score >= settings.skill_match_similarity_threshold:
            matched.add(norm)
            continue
        above_floor = sorted(
            (score, resume_norm) for score, resume_norm in scored if score >= settings.skill_match_ambiguous_floor
        )
        above_floor.sort(key=lambda pair: -pair[0])
        top_candidates = above_floor[:AMBIGUOUS_CANDIDATES_PER_JD_SKILL]
        if top_candidates:
            ambiguous_candidates[norm] = [resume_lookup[resume_norm] for _, resume_norm in top_candidates]
    return matched, ambiguous_candidates


def _llm_fallback_pass(
    llm_adapter: LLMAdapter, jd_lookup: dict[str, str], ambiguous_candidates: dict[str, list[str]]
) -> set[str]:
    # Note on verdict stability: llm_fallback_match runs at temperature 0.0,
    # but that reduces rather than eliminates run-to-run variance for a
    # genuinely borderline pair - Anthropic (like other LLM providers)
    # doesn't guarantee bit-identical output across separate requests even
    # at temperature 0. A skill-gap score built on these verdicts can
    # therefore shift slightly between two runs of the identical
    # resume/JD pair when a pair sits right at the model's own decision
    # boundary. This mirrors the same named risk CLAUDE.md already flags
    # for evaluation scoring ("scoring consistency across repeated runs is
    # a named risk") and isn't something a single LLM call can fully
    # eliminate - accepted here as an inherent characteristic of this
    # design rather than something to engineer around.
    matched = set()
    for norm, candidates in ambiguous_candidates.items():
        jd_text = jd_lookup[norm]
        for resume_text in candidates:
            try:
                if llm_fallback_match(llm_adapter, jd_skill=jd_text, resume_skill=resume_text):
                    matched.add(norm)
                    break  # one confirmed match is enough; skip the rest
            except Exception:
                # Fail open per-candidate: worst case this one candidate
                # contributes nothing, same as if it had never cleared the
                # floor. This is a best-effort enrichment call, never
                # session/request-blocking.
                continue
    return matched


def compute(
    resume: Resume, jd: JobDescription, embedding_adapter: EmbeddingAdapter, llm_adapter: LLMAdapter
) -> dict:
    resume_lookup = {s.strip().lower(): s for s in resume.structured_data.get("skills", [])}
    required_lookup = {s.strip().lower(): s for s in jd.structured_data.get("required_skills", [])}
    preferred_lookup = {s.strip().lower(): s for s in jd.structured_data.get("preferred_skills", [])}

    resume_canonical = {canonicalize(n) for n in resume_lookup}
    all_jd_norms = set(required_lookup) | set(preferred_lookup)
    exact_matched = {n for n in all_jd_norms if canonicalize(n) in resume_canonical}
    unmatched_norms = [n for n in all_jd_norms if n not in exact_matched]
    jd_text_lookup = {**required_lookup, **preferred_lookup}
    semantic_matched, ambiguous_candidates = _semantic_match(
        unmatched_norms, jd_text_lookup, resume_lookup, embedding_adapter
    )
    llm_matched = _llm_fallback_pass(llm_adapter, jd_text_lookup, ambiguous_candidates)
    matched_norms = exact_matched | semantic_matched | llm_matched

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
