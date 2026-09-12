"""Phase 4a adaptive interview graph.

Cyclic LangGraph state machine: Question Generator -> Interviewer (pass-through)
-> Evaluator -> adaptive difficulty adjustment, looping back into Question
Generator until the plan's question_count is reached (CLAUDE.md - "Question
Generator -> Interviewer -> Evaluator cycles repeatedly ... until the plan's
exit condition is met").

One compiled graph handles both REST entry points:
  - "start"  (POST /interview-sessions)          -> generate_question -> deliver_question -> END
  - "answer" (POST /interview-sessions/{id}/answer) -> evaluate_answer -> adjust_difficulty -> one of three
    branches: generate_followup (CE-c, same-topic probe on a specific gap) -> deliver_question -> END;
    generate_question (next main topic) -> deliver_question -> END; or straight to END if done.

The adjust_difficulty -> generate_question/generate_followup conditional edge is
the actual cycle: a single graph.invoke() call for an "answer" request both
scores the current turn and (if the session isn't finished) produces the next
question in one pass. Each HTTP call still stops at END to hand control back to
the human between turns. Phase 4b adds resumability at the app level (a
Redis-backed live state store in interview_session_service.py/
interview_session_state_repository.py, reconciled against Postgres) rather
than via a LangGraph-native checkpointer - this graph itself remains stateless
between invoke() calls.

CE-c note: difficulty adjustment (compute_next_difficulty) and follow-up
triggering are independently computed in adjust_difficulty_node - the former
runs first and unconditionally, on every turn, follow-up or not; the latter is
a separate decision read afterward from the same evaluation dict. They are not
branches of each other.
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
    # CE-a: each entry is {"topic": str, "project": dict | None} - project is
    # non-None only for a slot the Interview Planner tagged grounded_in_project.
    topic_queue: list[dict]
    current_difficulty: int
    turn_index: int
    total_questions: int

    # inputs for the "answer" path
    question_text: str | None
    answer_text: str | None
    # CE-c: topic of the turn just answered, and its follow-up budget usage
    # so far - fresh inputs threaded in from live_state on every "answer"
    # invocation, same as question_text/answer_text (this graph is stateless
    # between invoke() calls, per the module docstring).
    current_topic: str | None
    topic_number: int
    followup_count: int

    # cost cap (Phase 4d): accumulated_cost_usd is the running total carried
    # in from the caller (0.0 for a new session) and bumped by each node
    # that calls the LLM; cost_cap_usd is a per-session constant snapshotted
    # from settings.interview_session_max_cost_usd at session start.
    accumulated_cost_usd: float
    cost_cap_usd: float

    # outputs
    next_topic: str | None
    next_question_text: str | None
    evaluation: dict | None
    is_followup: bool
    done: bool
    # CE-c: internal routing signal read by _route_after_adjust only - not
    # consumed outside the graph.
    will_follow_up: bool
    stop_reason: Literal["completed", "cost_cap_exceeded"] | None


# CE-c: max same-topic follow-ups before the interviewer moves on
# regardless of what the Evaluator flags - see adjust_difficulty_node.
FOLLOWUP_LIMIT_PER_TOPIC = 2


def _route_entry(state: InterviewGraphState) -> str:
    return "start" if state["action"] == "start" else "answer"


def _route_after_adjust(state: InterviewGraphState) -> str:
    if state["done"]:
        return "finish"
    return "followup" if state["will_follow_up"] else "loop"


def build_interview_graph(llm: LLMAdapter):
    def generate_question_node(state: InterviewGraphState) -> dict:
        topic_queue = list(state["topic_queue"])
        entry = topic_queue.pop(0)
        result = generate_question(
            llm,
            topic=entry["topic"],
            difficulty=state["current_difficulty"],
            candidate_level=state["plan"]["candidate_level"],
            asked_questions=state["asked_questions"],
            project=entry.get("project"),
        )
        cost_delta = llm.last_usage.cost_usd if llm.last_usage else 0.0
        return {
            "topic_queue": topic_queue,
            "next_topic": entry["topic"],
            "next_question_text": result["question_text"],
            "accumulated_cost_usd": state["accumulated_cost_usd"] + cost_delta,
            # CE-c: a genuinely new topic slot - budget and is_followup reset,
            # topic_number advances. Never touched by the follow-up branch.
            "is_followup": False,
            "followup_count": 0,
            "topic_number": state["topic_number"] + 1,
        }

    def generate_followup_node(state: InterviewGraphState) -> dict:
        # CE-c: same-topic probe on the specific gap the Evaluator named -
        # does NOT pop topic_queue and does NOT touch project grounding
        # (continuity comes from quoting the original question verbatim,
        # not from re-threading CE-a's project data through a second path).
        evaluation = state["evaluation"]
        result = generate_question(
            llm,
            topic=state["current_topic"],
            difficulty=state["current_difficulty"],
            candidate_level=state["plan"]["candidate_level"],
            asked_questions=state["asked_questions"],
            followup_context={
                "original_question": state["question_text"],
                "original_answer": state["answer_text"],
                "followup_reason": evaluation["followup_reason"],
            },
        )
        cost_delta = llm.last_usage.cost_usd if llm.last_usage else 0.0
        return {
            "next_topic": state["current_topic"],
            "next_question_text": result["question_text"],
            "accumulated_cost_usd": state["accumulated_cost_usd"] + cost_delta,
            "is_followup": True,
            "followup_count": state["followup_count"] + 1,
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
        cost_delta = llm.last_usage.cost_usd if llm.last_usage else 0.0
        return {"evaluation": result, "accumulated_cost_usd": state["accumulated_cost_usd"] + cost_delta}

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
        # Reactive cost cap (CLAUDE.md - "the interview loop needs a
        # timeout/exit condition, not just a natural completion path"):
        # checked once per turn, after this turn's calls have already
        # completed, before deciding whether to loop back for another
        # question. A session can overshoot the cap by at most one turn's
        # worth of calls; it cannot loop indefinitely past it. This applies
        # identically whether the turn just evaluated was a follow-up or a
        # main-topic question - evaluate_answer_node's cost delta is already
        # folded into accumulated_cost_usd by the time this check runs,
        # regardless of which node produced the question being answered.
        cost_cap_exceeded = state["accumulated_cost_usd"] >= state["cost_cap_usd"]

        # CE-c: follow-up triggering, read from the same evaluation dict
        # difficulty adjustment just used above - independently computed,
        # not a branch of compute_next_difficulty. The cost cap and
        # natural-completion checks below only ever run in the non-followup
        # branch, so a session that just went over the cap can never take
        # the follow-up path - it falls straight through to the existing
        # done/stop_reason logic exactly as it did before CE-c.
        will_follow_up = (
            not cost_cap_exceeded
            and state["evaluation"].get("needs_followup", False)
            and state["followup_count"] < FOLLOWUP_LIMIT_PER_TOPIC
        )

        if will_follow_up:
            done = False
            stop_reason = None
        else:
            done = turn_index >= state["total_questions"] or not state["topic_queue"] or cost_cap_exceeded
            stop_reason = "cost_cap_exceeded" if cost_cap_exceeded else ("completed" if done else None)

        return {
            "current_difficulty": next_difficulty,
            "turn_index": turn_index,
            "done": done,
            "will_follow_up": will_follow_up,
            "stop_reason": stop_reason,
        }

    graph = StateGraph(InterviewGraphState)
    graph.add_node("generate_question", generate_question_node)
    graph.add_node("generate_followup", generate_followup_node)
    graph.add_node("deliver_question", deliver_question_node)
    graph.add_node("evaluate_answer", evaluate_answer_node)
    graph.add_node("adjust_difficulty", adjust_difficulty_node)

    graph.set_conditional_entry_point(
        _route_entry, {"start": "generate_question", "answer": "evaluate_answer"}
    )
    graph.add_edge("generate_question", "deliver_question")
    graph.add_edge("generate_followup", "deliver_question")
    graph.add_edge("deliver_question", END)
    graph.add_edge("evaluate_answer", "adjust_difficulty")
    graph.add_conditional_edges(
        "adjust_difficulty",
        _route_after_adjust,
        {"loop": "generate_question", "followup": "generate_followup", "finish": END},
    )

    return graph.compile()
