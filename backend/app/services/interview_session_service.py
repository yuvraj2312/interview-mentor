"""Phase 4a interview session orchestration.

Builds the LangGraph state machine's initial state from a persisted
InterviewPlan/InterviewSession, invokes it, and persists the result. Mirrors
interview_plan_service.py's synchronous, single-LLM-call-per-request shape,
and its convention of raising ValueError on malformed LLM output so the route
layer can turn it into a 502.
"""

import uuid

from sqlalchemy.orm import Session as DBSession

from app.llm_adapter import get_llm_adapter
from app.models import InterviewPlan, InterviewSession, InterviewTurn
from app.repositories import interview_session_repository
from app.workflows.interview_graph import build_interview_graph


def _plan_context(plan: InterviewPlan) -> dict:
    return {
        "candidate_level": plan.candidate_level,
        "difficulty_min": plan.difficulty_min,
        "difficulty_max": plan.difficulty_max,
    }


def _topic_queue_from_mix(topic_mix: list) -> list[str]:
    return [topic["topic"] for topic in topic_mix for _ in range(topic["question_count"])]


def start_session(db: DBSession, *, user_id: uuid.UUID, plan: InterviewPlan) -> tuple[InterviewSession, InterviewTurn]:
    topic_queue = _topic_queue_from_mix(plan.topic_mix)
    starting_difficulty = round((plan.difficulty_min + plan.difficulty_max) / 2)
    starting_difficulty = max(plan.difficulty_min, min(starting_difficulty, plan.difficulty_max))

    llm = get_llm_adapter()
    graph = build_interview_graph(llm)
    result = graph.invoke(
        {
            "action": "start",
            "plan": _plan_context(plan),
            "asked_questions": [],
            "topic_queue": topic_queue,
            "current_difficulty": starting_difficulty,
            "turn_index": 0,
            "total_questions": plan.question_count,
            "question_text": None,
            "answer_text": None,
            "next_topic": None,
            "next_question_text": None,
            "evaluation": None,
            "done": False,
        }
    )

    session = interview_session_repository.create(
        db,
        user_id=user_id,
        interview_plan_id=plan.id,
        total_questions=plan.question_count,
        current_difficulty=starting_difficulty,
        topic_queue=result["topic_queue"],
        asked_questions=[result["next_question_text"]],
    )
    turn = InterviewTurn(
        session_id=session.id,
        idx=0,
        topic=result["next_topic"],
        difficulty=starting_difficulty,
        question_text=result["next_question_text"],
    )
    db.add(turn)
    db.commit()
    db.refresh(session)
    db.refresh(turn)
    return session, turn


def submit_answer(
    db: DBSession, *, session: InterviewSession, plan: InterviewPlan, current_turn: InterviewTurn, answer_text: str
) -> tuple[InterviewSession, InterviewTurn, InterviewTurn | None]:
    """Evaluate current_turn's answer and advance the session.

    Returns (session, evaluated current_turn, next_turn | None). next_turn is
    None when the session is now complete.
    """
    llm = get_llm_adapter()
    graph = build_interview_graph(llm)
    result = graph.invoke(
        {
            "action": "answer",
            "plan": _plan_context(plan),
            "asked_questions": session.asked_questions,
            "topic_queue": session.topic_queue,
            "current_difficulty": session.current_difficulty,
            "turn_index": session.current_turn_index,
            "total_questions": session.total_questions,
            "question_text": current_turn.question_text,
            "answer_text": answer_text,
            "next_topic": None,
            "next_question_text": None,
            "evaluation": None,
            "done": False,
        }
    )

    evaluation = result["evaluation"]
    current_turn.answer_text = answer_text
    current_turn.technical_score = evaluation["technical_score"]
    current_turn.communication_score = evaluation["communication_score"]
    current_turn.completeness_score = evaluation["completeness_score"]
    current_turn.rationale = evaluation["rationale"]
    db.add(current_turn)

    if result["done"]:
        interview_session_repository.complete(db, session)
        db.commit()
        db.refresh(session)
        db.refresh(current_turn)
        return session, current_turn, None

    asked_questions = [*session.asked_questions, result["next_question_text"]]
    interview_session_repository.advance(
        db,
        session,
        current_difficulty=result["current_difficulty"],
        topic_queue=result["topic_queue"],
        asked_questions=asked_questions,
    )
    next_turn = InterviewTurn(
        session_id=session.id,
        idx=session.current_turn_index,
        topic=result["next_topic"],
        difficulty=result["current_difficulty"],
        question_text=result["next_question_text"],
    )
    db.add(next_turn)
    db.commit()
    db.refresh(session)
    db.refresh(current_turn)
    db.refresh(next_turn)
    return session, current_turn, next_turn
