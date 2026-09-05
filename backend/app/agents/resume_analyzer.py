"""Resume Analyzer agent.

Plain-function style mirroring app/interview.py - no LangGraph, no classes
(LangGraph orchestration is Phase 4+, not needed at this codebase maturity).
"""

from app.llm_adapter import LLMAdapter
from app.prompts import RESUME_ANALYSIS_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("skills", "experience", "education", "projects", "low_confidence_fields")


def analyze_resume(llm: LLMAdapter, resume_text: str) -> dict:
    prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text)
    raw = llm.generate(prompt, agent_name="resume_analyzer", temperature=0.2, max_tokens=2048)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed resume analysis object: {result!r}")
    return result
