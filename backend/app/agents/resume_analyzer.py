"""Resume Analyzer agent.

Plain-function style mirroring app/interview.py - no LangGraph, no classes
(LangGraph orchestration is Phase 4+, not needed at this codebase maturity).
"""

from app.llm_adapter import LLMAdapter
from app.prompts import RESUME_ANALYSIS_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("skills", "experience", "education", "projects", "low_confidence_fields")
LIST_KEYS = ("skills", "experience", "education", "projects", "low_confidence_fields")


def analyze_resume(llm: LLMAdapter, resume_text: str) -> dict:
    prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text)
    # 4096, not 2048: full verbatim bullet capture (every bullet, in full,
    # across every role/project - see RESUME_ANALYSIS_PROMPT) produces a much
    # larger response than the old 1-2 sentence summaries did, especially for
    # resumes with several roles/projects with several bullets each.
    raw = llm.generate(prompt, agent_name="resume_analyzer", temperature=0.2, max_tokens=4096)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed resume analysis object: {result!r}")

    # A genuinely empty section must come back as [], never None/omitted -
    # every downstream consumer (this system's own API responses, the
    # frontend, skill_gap_service's .get(key, []) calls) treats a present
    # empty list as "no data" and a null as an error condition, so null must
    # never leave this boundary (see 2026-09-13 empty-array display bug).
    for key in LIST_KEYS:
        if result[key] is None:
            result[key] = []
    return result
