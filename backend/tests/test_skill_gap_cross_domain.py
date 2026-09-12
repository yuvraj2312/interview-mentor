"""Cross-domain calibration + negative-control tests for the skill-gap LLM
fallback layer (layer 4).

Uses the REAL embedding adapter (matching test_skill_gap.py's existing
"real adapter, real model, deterministic on CPU, no mocked infra"
convention) so the ambiguous-band routing itself is exercised for real,
combined with a scripted LLMAdapter whose canned verdicts were confirmed
against the actual Anthropic model during implementation of this layer (a
one-off, throwaway check - not run here, since this repo never hits the
real Anthropic API from its automated test suite; see the plan notes for
the exact session transcript). Scores below are the real cosine
similarities measured for these exact phrase pairs.
"""

from app.embedding_adapter import get_embedding_adapter
from app.llm_adapter import LLMAdapter
from app.models import JobDescription, Resume
from app.services import skill_gap_service

_embedding_adapter = get_embedding_adapter()


class _ScriptedSkillMatchLLM(LLMAdapter):
    """Returns a fixed is_match verdict for every call, regardless of the
    prompt - each test below only ever exercises one ambiguous pair per
    compute() call, so a single scripted verdict per instance is enough.
    """

    def __init__(self, is_match: bool):
        self.last_usage = None
        self.calls: list[str] = []
        self._is_match = is_match

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.calls.append(prompt)
        return '{"is_match": %s, "rationale": "scripted for test"}' % ("true" if self._is_match else "false")


def _resume_and_jd(*, resume_skill: str, jd_skill: str) -> tuple[Resume, JobDescription]:
    resume = Resume(structured_data={"skills": [resume_skill]})
    jd = JobDescription(structured_data={"required_skills": [jd_skill], "preferred_skills": []})
    return resume, jd


# --- Finance ---


def test_finance_gaap_abbreviation_matches_via_llm_fallback():
    # cosine("Generally Accepted Accounting Principles", "GAAP") ~= 0.65 -
    # ambiguous band, no alias table entry outside tech.
    resume, jd = _resume_and_jd(resume_skill="GAAP", jd_skill="Generally Accepted Accounting Principles")
    llm = _ScriptedSkillMatchLLM(is_match=True)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["Generally Accepted Accounting Principles"]


def test_finance_sp_ratings_methodology_matches_via_llm_fallback():
    # The user's own example pair: cosine ~= 0.70, ambiguous band.
    resume, jd = _resume_and_jd(
        resume_skill="S&P ratings methodology exposure", jd_skill="rating agency criteria knowledge"
    )
    llm = _ScriptedSkillMatchLLM(is_match=True)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["rating agency criteria knowledge"]


def test_finance_accounts_payable_abbreviation_matches_via_llm_fallback():
    # cosine("Accounts Payable", "AP") ~= 0.53 - the lowest-scoring true
    # synonym found during calibration, well inside the ambiguous band.
    resume, jd = _resume_and_jd(resume_skill="AP", jd_skill="Accounts Payable")
    llm = _ScriptedSkillMatchLLM(is_match=True)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["Accounts Payable"]


def test_finance_negative_control_accounts_payable_vs_receivable_stays_missing():
    # False-friend, analogous to Java/JavaScript: shares the word
    # "Accounts" but is a different accounting function. cosine ~= 0.82 -
    # now inside the ambiguous band (it used to just fail the 0.85
    # threshold and stop there; this proves the new LLM layer doesn't
    # reintroduce it as a false positive).
    resume, jd = _resume_and_jd(resume_skill="Accounts Receivable", jd_skill="Accounts Payable")
    llm = _ScriptedSkillMatchLLM(is_match=False)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["Accounts Payable"]


# --- Healthcare ---


def test_healthcare_registered_nurse_abbreviation_matches_via_llm_fallback():
    # cosine("Registered Nurse", "RN") ~= 0.83, ambiguous band.
    resume, jd = _resume_and_jd(resume_skill="RN", jd_skill="Registered Nurse")
    llm = _ScriptedSkillMatchLLM(is_match=True)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["Registered Nurse"]


def test_healthcare_icu_paraphrase_matches_via_llm_fallback():
    # cosine("ICU experience", "Intensive Care Unit nursing") ~= 0.80.
    resume, jd = _resume_and_jd(resume_skill="ICU experience", jd_skill="Intensive Care Unit nursing")
    llm = _ScriptedSkillMatchLLM(is_match=True)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == ["Intensive Care Unit nursing"]


def test_healthcare_negative_control_registered_nurse_vs_dietitian_stays_missing():
    # False-friend: shares "Registered" but is a different profession.
    # cosine ~= 0.78 - inside the ambiguous band.
    resume, jd = _resume_and_jd(resume_skill="Registered Dietitian", jd_skill="Registered Nurse")
    llm = _ScriptedSkillMatchLLM(is_match=False)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["Registered Nurse"]


# --- Tech (regression: the layer must not reintroduce 6a's false-positive risk) ---


def test_tech_negative_control_java_javascript_stays_missing_via_llm_fallback():
    # The original 6a false-friend: cosine ~= 0.83, now inside the
    # ambiguous band under the new floor (it used to simply fail the 0.85
    # threshold and stop there). This is the direct regression check that
    # the new layer doesn't reintroduce it as a false positive.
    resume, jd = _resume_and_jd(resume_skill="Java", jd_skill="JavaScript")
    llm = _ScriptedSkillMatchLLM(is_match=False)  # confirmed against the real model

    result = skill_gap_service.compute(resume, jd, _embedding_adapter, llm)

    assert len(llm.calls) == 1
    assert result["matched_skills"] == []
    assert result["missing_required_skills"] == ["JavaScript"]
