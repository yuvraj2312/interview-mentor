"""Interviewer agent (CE-b).

Plain-function style mirroring app/agents/evaluator.py. Answers a candidate's
clarifying question about the CURRENT question only - this is a side-channel
call (see interview_session_service.handle_clarification), never scores an
answer and never advances the turn; that stays exclusively submit_answer()'s
job. Low temperature since this is a direct, grounded response, not creative
generation - same rationale evaluator.py gives for its own low temperature.
"""

from app.llm_adapter import LLMAdapter
from app.prompts import INTERVIEWER_CLARIFICATION_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("clarification_text",)


def answer_clarification(
    llm: LLMAdapter, *, topic: str, question_text: str, difficulty: int, clarifying_question: str
) -> dict:
    prompt = INTERVIEWER_CLARIFICATION_PROMPT.format(
        topic=topic, question_text=question_text, difficulty=difficulty, clarifying_question=clarifying_question
    )
    raw = llm.generate(prompt, agent_name="interviewer", temperature=0.3, max_tokens=300)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed interviewer clarification object: {result!r}")
    return result
