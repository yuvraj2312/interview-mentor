"""Phase 4b adaptive interview session state machine.

Pure, dependency-free definitions for the state machine documented in
docs/architecture.md: PLANNED -> IN_PROGRESS -> EVALUATING -> ADVANCING ->
IN_PROGRESS (next turn, loops) -> COMPLETE, with ABANDONED on inactivity.

Two of these six values are never actually persisted in Phase 4b:

- PLANNED: start_session() still generates the first question synchronously,
  in the same request that creates the session row, so there is no
  observable window between "session created" and "question delivered".
  This becomes real once starting a session is queued asynchronously.
- ADVANCING: adjust_difficulty -> generate_question happens inside a single
  graph.invoke() call today with no real pause point between them, so
  interview_session_service.submit_answer() brackets both EVALUATING and
  ADVANCING into one transient "evaluating" status written before that call.
  A genuine ADVANCING state needs a real pause point to push to, which
  arrives with the Phase 4c WebSocket channel.
"""

from enum import Enum
from typing import TypedDict


class SessionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    ADVANCING = "advancing"
    COMPLETE = "complete"
    ABANDONED = "abandoned"


TERMINAL_STATUSES = frozenset({SessionStatus.COMPLETE, SessionStatus.ABANDONED})
TRANSIENT_STATUSES = frozenset({SessionStatus.EVALUATING, SessionStatus.ADVANCING})


class LiveQuestion(TypedDict):
    turn_index: int
    topic: str
    difficulty: int
    question_text: str


class LiveSessionState(TypedDict):
    session_id: str
    status: str
    turn_index: int
    total_questions: int
    current_difficulty: int
    topic_queue: list[str]
    asked_questions: list[str]
    current_question: LiveQuestion | None
    last_activity_at: str  # ISO 8601 UTC
    # Phase 4d cost cap: total_cost_usd is the running spend for this
    # session; cost_cap_usd is the per-session limit snapshotted at session
    # start; stop_reason distinguishes a natural finish from a cap-triggered
    # one once the session is complete (None while still in progress).
    total_cost_usd: float
    cost_cap_usd: float
    stop_reason: str | None


def is_inactive(last_activity_at, *, now, timeout_seconds: int) -> bool:
    return (now - last_activity_at).total_seconds() > timeout_seconds
