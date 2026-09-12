"""Policy/wiring tests for skill_gap_service's LLM fallback layer (layer 4).

Uses a stub EmbeddingAdapter with hand-picked vectors to force specific
cosine scores deterministically. This is necessary (rather than using the
real model, as test_skill_gap.py otherwise prefers) because calibration
found the real model never naturally produces a score below ~0.43 for any
short professional-skill phrase pair tried - these tests need to exercise
the "confidently below the ambiguous floor" branch, which the real model's
observed score distribution can't reliably reach.
"""

import json

from app.embedding_adapter import EmbeddingAdapter
from app.llm_adapter import LLMAdapter
from app.models import JobDescription, Resume
from app.services import skill_gap_service


class _StubEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors[t] for t in texts]


# cosine([1, 0], [0, 1]) == 0.0 -> below the 0.35 floor
_BELOW_FLOOR_VECTORS = {"JD Low": [1.0, 0.0], "Resume Low": [0.0, 1.0]}
# cosine([1, 0], [0.99, 0.1411]) ~= 0.99 -> above the 0.85 threshold
_ABOVE_THRESHOLD_VECTORS = {"JD High": [1.0, 0.0], "Resume High": [0.99, 0.1411]}
# cosine([1, 0], [0.6, 0.8]) == 0.6 -> inside the ambiguous band
_AMBIGUOUS_VECTORS = {"JD Mid": [1.0, 0.0], "Resume Mid": [0.6, 0.8]}


class _TrackingLLM(LLMAdapter):
    def __init__(self, response: dict | str | None = None, *, raises: bool = False):
        self.last_usage = None
        self.calls: list[str] = []
        self._response = response
        self._raises = raises

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.calls.append(prompt)
        if self._raises:
            raise RuntimeError("simulated LLM failure")
        if isinstance(self._response, str):
            return self._response
        return json.dumps(self._response)


class _VerdictByResumeSkillLLM(LLMAdapter):
    """Scripted double whose verdict depends on which RESUME PHRASE appears
    in the prompt - lets a test express "distractor X says no, true match Y
    says yes" without needing separate compute() calls.
    """

    def __init__(self, verdicts: dict[str, bool]):
        self.last_usage = None
        self.calls: list[str] = []
        self._verdicts = verdicts

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.calls.append(prompt)
        for resume_skill, is_match in self._verdicts.items():
            if f"RESUME PHRASE: {resume_skill}" in prompt:
                return json.dumps({"is_match": is_match, "rationale": "scripted"})
        raise AssertionError(f"no scripted verdict for prompt: {prompt}")


def _resume_and_jd(*, resume_skill: str, jd_skill: str) -> tuple[Resume, JobDescription]:
    resume = Resume(structured_data={"skills": [resume_skill]})
    jd = JobDescription(structured_data={"required_skills": [jd_skill], "preferred_skills": []})
    return resume, jd


def test_below_floor_pair_never_calls_the_llm():
    resume, jd = _resume_and_jd(resume_skill="Resume Low", jd_skill="JD Low")
    llm = _TrackingLLM({"is_match": True, "rationale": "n/a"})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_BELOW_FLOOR_VECTORS), llm)

    assert llm.calls == []
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JD Low"]


def test_above_threshold_pair_never_calls_the_llm():
    resume, jd = _resume_and_jd(resume_skill="Resume High", jd_skill="JD High")
    llm = _TrackingLLM({"is_match": False, "rationale": "n/a"})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_ABOVE_THRESHOLD_VECTORS), llm)

    assert llm.calls == []
    assert result["matched_skills"] == ["JD High"]
    assert result["missing_required_skills"] == []


def test_ambiguous_pair_calls_llm_and_matches_on_true_verdict():
    resume, jd = _resume_and_jd(resume_skill="Resume Mid", jd_skill="JD Mid")
    llm = _TrackingLLM({"is_match": True, "rationale": "same underlying skill"})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_AMBIGUOUS_VECTORS), llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["JD Mid"]
    assert result["missing_required_skills"] == []


def test_ambiguous_pair_calls_llm_and_stays_missing_on_false_verdict():
    resume, jd = _resume_and_jd(resume_skill="Resume Mid", jd_skill="JD Mid")
    llm = _TrackingLLM({"is_match": False, "rationale": "different skills"})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_AMBIGUOUS_VECTORS), llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JD Mid"]


def test_llm_error_fails_open():
    resume, jd = _resume_and_jd(resume_skill="Resume Mid", jd_skill="JD Mid")
    llm = _TrackingLLM(raises=True)

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_AMBIGUOUS_VECTORS), llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JD Mid"]


def test_malformed_llm_json_fails_open():
    resume, jd = _resume_and_jd(resume_skill="Resume Mid", jd_skill="JD Mid")
    llm = _TrackingLLM({"is_match": True})  # missing required "rationale" key

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_AMBIGUOUS_VECTORS), llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JD Mid"]


# --- Multi-candidate (top-K) behavior: regression coverage for the
# 2026-09-12 finding that a single-best-candidate design let a narrowly
# higher-scoring distractor starve a real, lower-scoring match from ever
# reaching the LLM (e.g. "Investment Analysis" 0.713 outscoring "Critical
# Thinking" 0.681 against JD skill "Analytical skills"). ---


def _jd_and_multi_resume(*, jd_skill: str, resume_skills: list[str]) -> tuple[Resume, JobDescription]:
    resume = Resume(structured_data={"skills": resume_skills})
    jd = JobDescription(structured_data={"required_skills": [jd_skill], "preferred_skills": []})
    return resume, jd


# All below the 0.85 threshold (so none confidently matches on embeddings
# alone) and all above the 0.35 floor, ranked by cosine against [1, 0]:
# Distractor (0.80) > TrueMatch (0.60) > ThirdPlace (0.50) > FourthPlace
# (0.40, rank 4 - outside AMBIGUOUS_CANDIDATES_PER_JD_SKILL=3, must never
# be queried).
_RANKED_CANDIDATE_VECTORS = {
    "JD Skill": [1.0, 0.0],
    "Distractor": [0.80, (1 - 0.80**2) ** 0.5],
    "TrueMatch": [0.60, (1 - 0.60**2) ** 0.5],
    "ThirdPlace": [0.50, (1 - 0.50**2) ** 0.5],
    "FourthPlace": [0.40, (1 - 0.40**2) ** 0.5],
}


def test_lower_ranked_true_match_is_still_checked_despite_a_higher_scoring_distractor():
    resume, jd = _jd_and_multi_resume(
        jd_skill="JD Skill", resume_skills=["Distractor", "TrueMatch", "ThirdPlace", "FourthPlace"]
    )
    llm = _VerdictByResumeSkillLLM({"Distractor": False, "TrueMatch": True})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_RANKED_CANDIDATE_VECTORS), llm)

    assert result["matched_skills"] == ["JD Skill"]
    # short-circuits after the 2nd candidate confirms a match - never
    # reaches ThirdPlace or FourthPlace
    assert len(llm.calls) == 2


def test_only_top_3_candidates_are_ever_sent_to_the_llm():
    resume, jd = _jd_and_multi_resume(
        jd_skill="JD Skill", resume_skills=["Distractor", "TrueMatch", "ThirdPlace", "FourthPlace"]
    )
    # Top 3 (Distractor, TrueMatch, ThirdPlace) all say no; FourthPlace
    # would say yes if asked, but ranks below the cap and must never be
    # queried.
    llm = _VerdictByResumeSkillLLM({"Distractor": False, "TrueMatch": False, "ThirdPlace": False, "FourthPlace": True})

    result = skill_gap_service.compute(resume, jd, _StubEmbeddingAdapter(_RANKED_CANDIDATE_VECTORS), llm)

    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JD Skill"]
    assert len(llm.calls) == 3
    assert not any("RESUME PHRASE: FourthPlace" in call for call in llm.calls)
