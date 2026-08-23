"""Phase 4a adaptive interview graph.

Cyclic LangGraph state machine: Question Generator -> Interviewer (pass-through)
-> Evaluator -> adaptive difficulty adjustment, looping back into Question
Generator until the plan's question_count is reached (CLAUDE.md - "Question
Generator -> Interviewer -> Evaluator cycles repeatedly ... until the plan's
exit condition is met").

One compiled graph handles both REST entry points:
  - "start"  (POST /interview-sessions)          -> generate_question -> deliver_question -> END
  - "answer" (POST /interview-sessions/{id}/answer) -> evaluate_answer -> adjust_difficulty -> loop back into
    generate_question (if more turns remain) -> deliver_question -> END, or straight to END if done.

The adjust_difficulty -> generate_question conditional edge is the actual cycle: a
single graph.invoke() call for an "answer" request both scores the current turn
and (if the session isn't finished) produces the next question in one pass.
Each HTTP call still stops at END to hand control back to the human between
turns. Phase 4b adds resumability at the app level (a Redis-backed live state
store in interview_session_service.py/interview_session_state_repository.py,
reconciled against Postgres) rather than via a LangGraph-native checkpointer -
this graph itself remains stateless between invoke() calls.
"""

from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.evaluator import evaluate_answer
from app.agents.question_generator import generate_question
from app.llm_adapter import LLMAdapter
from app.workflows.difficulty import compute_next_difficulty


class InterviewPlanContext(TypedDict):
    candidate_level: str
    difficulty_min: int
    difficulty_max: int


class InterviewGraphState(TypedDict):
    action: Literal["start", "answer"]
    plan: InterviewPlanContext
    asked_questions: list[str]
    topic_queue: list[str]
    current_difficulty: int
    turn_index: int
    total_questions: int

    # inputs for the "answer" path
    question_text: str | None
    answer_text: str | None

    # outputs
    next_topic: str | None
    next_question_text: str | None
    evaluation: dict | None
    done: bool


def _route_entry(state: InterviewGraphState) -> str:
    return "start" if state["action"] == "start" else "answer"


def _route_after_adjust(state: InterviewGraphState) -> str:
    return "finish" if state["done"] else "loop"


def build_interview_graph(llm: LLMAdapter):
    def generate_question_node(state: InterviewGraphState) -> dict:
        topic_queue = list(state["topic_queue"])
        topic = topic_queue.pop(0)
        result = generate_question(
            llm,
            topic=topic,
            difficulty=state["current_difficulty"],
            candidate_level=state["plan"]["candidate_level"],
            asked_questions=state["asked_questions"],
        )
        return {
            "topic_queue": topic_queue,
            "next_topic": topic,
            "next_question_text": result["question_text"],
        }

    def deliver_question_node(state: InterviewGraphState) -> dict:
        # Deterministic pass-through: no LLM call in Phase 4a. Kept as an
        # explicit node so the graph topology matches the architecture's
        # 3-stage cycle and a later phase can add real persona delivery
        # here without changing the graph shape.
        return {}

    def evaluate_answer_node(state: InterviewGraphState) -> dict:
        result = evaluate_answer(
            llm,
            question_text=state["question_text"],
            answer_text=state["answer_text"],
            difficulty=state["current_difficulty"],
        )
        return {"evaluation": result}

    def adjust_difficulty_node(state: InterviewGraphState) -> dict:
        evaluation = state["evaluation"]
        plan = state["plan"]
        next_difficulty = compute_next_difficulty(
            state["current_difficulty"],
            evaluation["technical_score"],
            evaluation["communication_score"],
            evaluation["completeness_score"],
            plan["difficulty_min"],
            plan["difficulty_max"],
        )
        turn_index = state["turn_index"] + 1
        done = turn_index >= state["total_questions"] or not state["topic_queue"]
        return {"current_difficulty": next_difficulty, "turn_index": turn_index, "done": done}

    graph = StateGraph(InterviewGraphState)
    graph.add_node("generate_question", generate_question_node)
    graph.add_node("deliver_question", deliver_question_node)
    graph.add_node("evaluate_answer", evaluate_answer_node)
    graph.add_node("adjust_difficulty", adjust_difficulty_node)

    graph.set_conditional_entry_point(
        _route_entry, {"start": "generate_question", "answer": "evaluate_answer"}
    )
    graph.add_edge("generate_question", "deliver_question")
    graph.add_edge("deliver_question", END)
    graph.add_edge("evaluate_answer", "adjust_difficulty")
    graph.add_conditional_edges(
        "adjust_difficulty", _route_after_adjust, {"loop": "generate_question", "finish": END}
    )

    return graph.compile()
