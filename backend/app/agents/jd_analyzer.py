"""JD Analyzer agent.

Plain-function style mirroring app/interview.py - no LangGraph, no classes
(LangGraph orchestration is Phase 4+, not needed at this codebase maturity).
"""

from app.llm_adapter import LLMAdapter
from app.prompts import JD_ANALYSIS_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("required_skills", "preferred_skills", "seniority_level", "low_confidence_fields")


def analyze_job_description(llm: LLMAdapter, jd_text: str) -> dict:
    prompt = JD_ANALYSIS_PROMPT.format(jd_text=jd_text)
    raw = llm.generate(prompt, temperature=0.2, max_tokens=1024)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed JD analysis object: {result!r}")
    return result
