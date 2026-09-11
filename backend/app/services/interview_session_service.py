"""Phase 4a/4b interview session orchestration.

Builds the LangGraph state machine's initial state from a persisted
InterviewPlan/InterviewSession, invokes it, and persists the result. Mirrors
interview_plan_service.py's synchronous, single-LLM-call-per-request shape,
and its convention of raising ValueError on malformed LLM output so the route
layer can turn it into a 502.

Phase 4b adds a Redis-backed live state store (interview_session_state_repository)
as the fast, primary read path for in-progress turn continuity, with Postgres
staying the durable source of truth for completed turns/final results and a
coarse session status. get_live_state() is the single reconciliation point
between the two stores - see its docstring for the recovery rules.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.agents.interviewer import answer_clarification
from app.core.config import settings
from app.llm_adapter import get_llm_adapter
from app.models import InterviewPlan, InterviewSession, InterviewTurn
from app.repositories import interview_session_repository
from app.repositories import interview_session_state_repository as state_repo
from app.services import skill_profile_service
from app.workflows.interview_graph import build_interview_graph
from app.workflows.session_state import (
    TERMINAL_STATUSES,
    LiveQuestion,
    LiveSessionState,
    SessionStatus,
    is_inactive,
)


class InterviewSessionCompleteError(Exception):
    """Session is already COMPLETE; no further answers/state transitions apply."""

    def __init__(self, session_id: uuid.UUID):
        self.session_id = session_id
        super().__init__(f"Interview session {session_id} is already complete")


class InterviewSessionAbandonedError(Exception):
    """Session is (or was just now flagged) ABANDONED by the lazy inactivity check."""

    def __init__(self, session_id: uuid.UUID):
        self.session_id = session_id
        super().__init__(f"Interview session {session_id} was abandoned due to inactivity")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# CE-b: how many clarification exchanges a candidate gets per question
# before the backend declines and prompts them to just answer.
CLARIFICATION_LIMIT_PER_QUESTION = 2
CLARIFICATION_DECLINE_MESSAGE = (
    "You've used your clarifications for this question - go ahead and answer with your best understanding."
)


def _plan_context(plan: InterviewPlan) -> dict:
    return {
        "candidate_level": plan.candidate_level,
        "difficulty_min": plan.difficulty_min,
        "difficulty_max": plan.difficulty_max,
    }


def _topic_queue_from_mix(topic_mix: list) -> list[dict]:
    return [
        {"topic": entry["topic"], "project": entry.get("project") if entry.get("grounded_in_project") else None}
        for entry in topic_mix
        for _ in range(entry["question_count"])
    ]


def _live_question(turn: InterviewTurn) -> LiveQuestion:
    return {
        "turn_index": turn.idx,
        "topic": turn.topic,
        "difficulty": turn.difficulty,
        "question_text": turn.question_text,
        "clarification_count": 0,
    }


def _state_blob(
    session_id: uuid.UUID,
    *,
    status: str,
    turn_index: int,
    total_questions: int,
    current_difficulty: int,
    topic_queue: list[dict],
    asked_questions: list[str],
    current_question: LiveQuestion | None,
    last_activity_at: datetime,
    total_cost_usd: float,
    cost_cap_usd: float,
    stop_reason: str | None,
) -> LiveSessionState:
    return {
        "session_id": str(session_id),
        "status": status,
        "turn_index": turn_index,
        "total_questions": total_questions,
        "current_difficulty": current_difficulty,
        "topic_queue": topic_queue,
        "asked_questions": asked_questions,
        "current_question": current_question,
        "last_activity_at": last_activity_at.isoformat(),
        "total_cost_usd": total_cost_usd,
        "cost_cap_usd": cost_cap_usd,
        "stop_reason": stop_reason,
    }


def _terminal_blob(session: InterviewSession) -> LiveSessionState:
    return _state_blob(
        session.id,
        status=session.status,
        turn_index=session.current_turn_index,
        total_questions=session.total_questions,
        current_difficulty=session.current_difficulty,
        topic_queue=session.topic_queue,
        asked_questions=session.asked_questions,
        current_question=None,
        last_activity_at=session.last_activity_at,
        total_cost_usd=session.total_cost_usd,
        cost_cap_usd=session.cost_cap_usd,
        stop_reason=session.stop_reason,
    )


def _rehydrate_in_progress(session: InterviewSession) -> LiveSessionState:
    current_turn = next(t for t in session.turns if t.idx == session.current_turn_index)
    blob = _state_blob(
        session.id,
        status=SessionStatus.IN_PROGRESS.value,
        turn_index=session.current_turn_index,
        total_questions=session.total_questions,
        current_difficulty=session.current_difficulty,
        topic_queue=session.topic_queue,
        asked_questions=session.asked_questions,
        current_question=_live_question(current_turn),
        last_activity_at=session.last_activity_at,
        total_cost_usd=session.total_cost_usd,
        cost_cap_usd=session.cost_cap_usd,
        stop_reason=session.stop_reason,
    )
    state_repo.save(blob)
    return blob


def _is_stuck_transient(state: LiveSessionState) -> bool:
    if state["status"] not in (SessionStatus.EVALUATING.value, SessionStatus.ADVANCING.value):
        return False
    last_activity = datetime.fromisoformat(state["last_activity_at"])
    return is_inactive(
        last_activity, now=_now(), timeout_seconds=settings.interview_session_stuck_transient_seconds
    )


def get_live_state(db: DBSession, session: InterviewSession) -> LiveSessionState:
    """Reconcile Redis's live state against Postgres for `session`.

    Postgres is always the newer truth when the two disagree, since every
    Postgres mutation lands in one atomic db.commit() per request, while a
    Redis write can be left stale or missing by a request that crashed or
    partially failed. Reconciliation order:

    1. Postgres terminal check, unconditional: if session.status is already
       complete/abandoned, that wins outright over any Redis hit - it also
       self-heals the case where Postgres committed complete/abandoned but
       the request's own follow-up Redis delete/save afterward failed.
    2. A Redis hit is only trusted if it isn't a *stuck transient*: an
       "evaluating"/"advancing" marker older than
       interview_session_stuck_transient_seconds means a prior request wrote
       that marker and then crashed (LLM error, process death) before ever
       writing a final status, so it's orphaned, not a real in-flight
       request.
    3. On a miss (absent, or discarded as stuck), rebuild from Postgres and
       repopulate Redis.
    4. Only once state is trustworthy and non-terminal does the inactivity
       check run.

    This is called by both submit_answer() and GET /interview-sessions/{id}/state,
    which deliberately makes the GET non-pure-read: it's the check-on-access
    abandonment trigger, and now also the disagreement-repair trigger.
    """
    if session.status in (SessionStatus.COMPLETE.value, SessionStatus.ABANDONED.value):
        state_repo.delete(session.id)
        return _terminal_blob(session)

    state = state_repo.load(session.id)
    if state is not None and _is_stuck_transient(state):
        state = None
    if state is None:
        state = _rehydrate_in_progress(session)

    last_activity = datetime.fromisoformat(state["last_activity_at"])
    if is_inactive(
        last_activity, now=_now(), timeout_seconds=settings.interview_session_inactivity_timeout_seconds
    ):
        interview_session_repository.abandon(db, session)
        db.commit()
        db.refresh(session)
        state_repo.delete(session.id)
        return {**state, "status": SessionStatus.ABANDONED.value}

    return state


def reconcile_stale_sessions(db: DBSession, sessions: list[InterviewSession]) -> None:
    """Run the check-on-access abandonment check for every non-terminal
    session in a list result, so a stale IN_PROGRESS session flips to
    ABANDONED as soon as it's viewed in a list, not only when its own
    state/WS endpoint is opened directly (see get_live_state())."""
    for session in sessions:
        if session.status not in TERMINAL_STATUSES:
            get_live_state(db, session)


def handle_clarification(db: DBSession, *, session: InterviewSession, question: str) -> dict:
    """Answer a candidate's clarifying question about the CURRENT question.

    A side-channel, not a turn: never calls submit_answer()/the LangGraph,
    never scores, never touches current_turn_index/topic_queue/InterviewTurn.
    Capped at CLARIFICATION_LIMIT_PER_QUESTION per question (tracked on
    LiveQuestion, which already resets every turn advance - see
    _live_question()). Bypasses build_interview_graph() entirely, so it also
    bypasses adjust_difficulty_node's cost-cap check - that check is
    replicated here (against the *pre-call* total, declining for free rather
    than spending then discarding) so a burst of clarifications still can't
    blow through the per-session cap. Deliberately does not force the
    session to "complete" if this call pushes total_cost_usd over the cap:
    the current turn has no evaluation yet, so _build_summary() would break
    on it. The bumped total_cost_usd is persisted regardless, so the next
    real submit_answer() call's existing, unmodified cap check trips there
    instead - the interview still can't run indefinitely past the cap.

    Returns a dict: {clarification_text, clarifications_used,
    clarifications_remaining, declined}.
    """
    live_state = get_live_state(db, session)

    if live_state["status"] == SessionStatus.COMPLETE.value:
        raise InterviewSessionCompleteError(session.id)
    if live_state["status"] == SessionStatus.ABANDONED.value:
        raise InterviewSessionAbandonedError(session.id)

    current_question = live_state["current_question"]
    clarifications_used = current_question.get("clarification_count", 0)
    at_cost_cap = live_state["total_cost_usd"] >= live_state["cost_cap_usd"]

    if clarifications_used >= CLARIFICATION_LIMIT_PER_QUESTION or at_cost_cap:
        return {
            "clarification_text": CLARIFICATION_DECLINE_MESSAGE,
            "clarifications_used": clarifications_used,
            "clarifications_remaining": max(0, CLARIFICATION_LIMIT_PER_QUESTION - clarifications_used),
            "declined": True,
        }

    llm = get_llm_adapter(db, session_id=session.id)
    result = answer_clarification(
        llm,
        topic=current_question["topic"],
        question_text=current_question["question_text"],
        difficulty=current_question["difficulty"],
        clarifying_question=question,
    )

    cost_delta = llm.last_usage.cost_usd if llm.last_usage else 0.0
    total_cost_usd = live_state["total_cost_usd"] + cost_delta
    clarifications_used += 1

    interview_session_repository.bump_cost(db, session, total_cost_usd=total_cost_usd)
    db.commit()
    db.refresh(session)

    state_repo.save(
        {
            **live_state,
            "current_question": {**current_question, "clarification_count": clarifications_used},
            "total_cost_usd": total_cost_usd,
            "last_activity_at": session.last_activity_at.isoformat(),
        }
    )

    return {
        "clarification_text": result["clarification_text"],
        "clarifications_used": clarifications_used,
        "clarifications_remaining": max(0, CLARIFICATION_LIMIT_PER_QUESTION - clarifications_used),
        "declined": False,
    }


def start_session(db: DBSession, *, user_id: uuid.UUID, plan: InterviewPlan) -> tuple[InterviewSession, InterviewTurn]:
    topic_queue = _topic_queue_from_mix(plan.topic_mix)
    starting_difficulty = round((plan.difficulty_min + plan.difficulty_max) / 2)
    starting_difficulty = max(plan.difficulty_min, min(starting_difficulty, plan.difficulty_max))

    cost_cap_usd = settings.interview_session_max_cost_usd

    # Row created (flushed, not committed) before the graph call so its id
    # exists in Postgres for the LLM adapter's trace insert to reference:
    # AnthropicAdapter.generate() flushes its llm_calls row immediately
    # per call (not deferred to this function's later db.commit()), and
    # llm_calls.session_id has an FK on interview_sessions.id.
    session = interview_session_repository.create(
        db,
        user_id=user_id,
        interview_plan_id=plan.id,
        total_questions=plan.question_count,
        current_difficulty=starting_difficulty,
        topic_queue=topic_queue,
        asked_questions=[],
        cost_cap_usd=cost_cap_usd,
    )

    llm = get_llm_adapter(db, session_id=session.id)
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
            "accumulated_cost_usd": 0.0,
            "cost_cap_usd": cost_cap_usd,
            "next_topic": None,
            "next_question_text": None,
            "evaluation": None,
            "done": False,
            "stop_reason": None,
        }
    )

    session.topic_queue = result["topic_queue"]
    session.asked_questions = [result["next_question_text"]]
    session.total_cost_usd = result["accumulated_cost_usd"]
    db.add(session)

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

    state_repo.save(
        _state_blob(
            session.id,
            status=SessionStatus.IN_PROGRESS.value,
            turn_index=0,
            total_questions=session.total_questions,
            current_difficulty=starting_difficulty,
            topic_queue=result["topic_queue"],
            asked_questions=session.asked_questions,
            current_question=_live_question(turn),
            last_activity_at=session.last_activity_at,
            total_cost_usd=session.total_cost_usd,
            cost_cap_usd=session.cost_cap_usd,
            stop_reason=None,
        )
    )
    return session, turn


def submit_answer(
    db: DBSession, *, session: InterviewSession, plan: InterviewPlan, current_turn: InterviewTurn, answer_text: str
) -> tuple[InterviewSession, InterviewTurn, InterviewTurn | None]:
    """Evaluate current_turn's answer and advance the session.

    Returns (session, evaluated current_turn, next_turn | None). next_turn is
    None when the session is now complete.
    """
    live_state = get_live_state(db, session)

    if live_state["status"] == SessionStatus.COMPLETE.value:
        raise InterviewSessionCompleteError(session.id)
    if live_state["status"] == SessionStatus.ABANDONED.value:
        raise InterviewSessionAbandonedError(session.id)

    # EVALUATING/ADVANCING bracket: adjust_difficulty -> generate_question is
    # one uninterrupted graph.invoke() pass below, with no real pause point
    # between them, so both are folded into a single transient "evaluating"
    # status written just before that call. See workflows/session_state.py
    # for why a genuine ADVANCING state is deferred to the Phase 4c
    # WebSocket channel.
    state_repo.save({**live_state, "status": SessionStatus.EVALUATING.value, "last_activity_at": _now().isoformat()})

    llm = get_llm_adapter(db, session_id=session.id)
    graph = build_interview_graph(llm)
    result = graph.invoke(
        {
            "action": "answer",
            "plan": _plan_context(plan),
            "asked_questions": live_state["asked_questions"],
            "topic_queue": live_state["topic_queue"],
            "current_difficulty": live_state["current_difficulty"],
            "turn_index": live_state["turn_index"],
            "total_questions": live_state["total_questions"],
            "question_text": live_state["current_question"]["question_text"],
            "answer_text": answer_text,
            "accumulated_cost_usd": live_state["total_cost_usd"],
            "cost_cap_usd": live_state["cost_cap_usd"],
            "next_topic": None,
            "next_question_text": None,
            "evaluation": None,
            "done": False,
            "stop_reason": None,
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
        interview_session_repository.complete(
            db, session, total_cost_usd=result["accumulated_cost_usd"], stop_reason=result["stop_reason"]
        )
        # current_turn's evaluation scores above are only db.add()-ed, not
        # flushed - SessionLocal runs autoflush=False (app/db.py), so an
        # explicit flush here is required for recompute_for_user()'s fresh
        # query to see this session's final turn.
        db.flush()
        skill_profile_service.recompute_for_user(db, session.user_id)
        db.commit()
        db.refresh(session)
        db.refresh(current_turn)
        state_repo.delete(session.id)
        return session, current_turn, None

    asked_questions = [*live_state["asked_questions"], result["next_question_text"]]
    interview_session_repository.advance(
        db,
        session,
        current_difficulty=result["current_difficulty"],
        topic_queue=result["topic_queue"],
        asked_questions=asked_questions,
        total_cost_usd=result["accumulated_cost_usd"],
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

    state_repo.save(
        _state_blob(
            session.id,
            status=SessionStatus.IN_PROGRESS.value,
            turn_index=session.current_turn_index,
            total_questions=session.total_questions,
            current_difficulty=session.current_difficulty,
            topic_queue=session.topic_queue,
            asked_questions=session.asked_questions,
            current_question=_live_question(next_turn),
            last_activity_at=session.last_activity_at,
            total_cost_usd=session.total_cost_usd,
            cost_cap_usd=session.cost_cap_usd,
            stop_reason=None,
        )
    )
    return session, current_turn, next_turn
