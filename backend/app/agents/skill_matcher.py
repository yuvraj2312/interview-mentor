"""Skill-matcher agent: LLM fallback for skill-gap pairs whose embedding
similarity falls in the ambiguous middle band - not confidently matched,
not confidently unrelated (see skill_gap_service.py). Plain-function style
mirroring app/agents/evaluator.py.
"""

from app.llm_adapter import LLMAdapter
from app.prompts import SKILL_MATCH_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("is_match", "rationale")


def llm_fallback_match(llm: LLMAdapter, *, jd_skill: str, resume_skill: str) -> bool:
    prompt = SKILL_MATCH_PROMPT.format(jd_skill=jd_skill, resume_skill=resume_skill)
    # temperature 0.0: a binary classification with one defensible right
    # answer per pair, not generation that benefits from variance.
    raw = llm.generate(prompt, agent_name="skill_matcher", temperature=0.0, max_tokens=200)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed skill_matcher object: {result!r}")
    return bool(result["is_match"])
