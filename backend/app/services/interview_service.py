"""Thin wrapper around interview.py + llm_adapter.py for api/sessions.py.

Kept separate from app.interview so routes call a service rather than the
raw Phase-0 module directly; interview.py itself is left untouched since
its LLM-parsing logic is Phase-0-verified and out of scope for Phase 1.
"""

from sqlalchemy.orm import Session as DBSession

from app.interview import evaluate_answer as _evaluate_answer
from app.interview import generate_questions as _generate_questions
from app.llm_adapter import get_llm_adapter


def generate_questions(db: DBSession, resume_text: str, jd_text: str) -> list[dict]:
    llm = get_llm_adapter(db)
    return _generate_questions(llm, resume_text, jd_text)


def evaluate_answer(db: DBSession, question_text: str, answer_text: str) -> dict:
    llm = get_llm_adapter(db)
    return _evaluate_answer(llm, question_text, answer_text)
