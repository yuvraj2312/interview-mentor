"""Hardcoded ask -> evaluate loop logic for the Phase 0 vertical slice.

No adaptive difficulty selection and no multi-agent orchestration here -
that's Phase 4 (LangGraph cyclic state machine). This is a plain 3-question
loop: generate all 3 questions once, then evaluate answers one at a time.
"""

import json
import re

from app.llm_adapter import LLMAdapter
from app.prompts import EVALUATION_PROMPT, QUESTION_GENERATION_PROMPT

QUESTIONS_PER_SESSION = 3


def _parse_json(raw: str) -> dict | list:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_questions(llm: LLMAdapter, resume_text: str, jd_text: str) -> list[dict]:
    prompt = QUESTION_GENERATION_PROMPT.format(resume_text=resume_text, jd_text=jd_text)
    raw = llm.generate(prompt, agent_name="legacy_question_generator", temperature=0.7, max_tokens=1024)
    questions = _parse_json(raw)

    if not isinstance(questions, list) or len(questions) != QUESTIONS_PER_SESSION:
        raise ValueError(f"Expected {QUESTIONS_PER_SESSION} questions, got: {raw!r}")
    for q in questions:
        if not all(k in q for k in ("topic", "difficulty", "question")):
            raise ValueError(f"Malformed question object: {q!r}")
    return questions


def evaluate_answer(llm: LLMAdapter, question_text: str, answer_text: str) -> dict:
    # Low temperature for consistent, auditable scoring (BRD S14 risk).
    prompt = EVALUATION_PROMPT.format(question_text=question_text, answer_text=answer_text)
    raw = llm.generate(prompt, agent_name="legacy_evaluator", temperature=0.2, max_tokens=512)
    evaluation = _parse_json(raw)

    required = ("technical_score", "communication_score", "completeness_score", "rationale")
    if not all(k in evaluation for k in required):
        raise ValueError(f"Malformed evaluation object: {evaluation!r}")
    return evaluation
