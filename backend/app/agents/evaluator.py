"""Evaluator agent (Phase 4a).

Plain-function style mirroring app/agents/jd_analyzer.py. Low temperature per
CLAUDE.md ("Evaluation calls should use low temperature / fixed rubric
prompts - scoring consistency across repeated runs is a named risk").
"""

from app.llm_adapter import LLMAdapter
from app.prompts import ADAPTIVE_EVALUATION_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("technical_score", "communication_score", "completeness_score", "rationale")


def evaluate_answer(llm: LLMAdapter, *, question_text: str, answer_text: str, difficulty: int) -> dict:
    prompt = ADAPTIVE_EVALUATION_PROMPT.format(
        question_text=question_text, answer_text=answer_text, difficulty=difficulty
    )
    raw = llm.generate(prompt, temperature=0.2, max_tokens=512)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed evaluation object: {result!r}")
    return result
