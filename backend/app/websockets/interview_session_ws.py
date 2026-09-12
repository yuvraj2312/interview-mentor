"""Phase 4c live interview WebSocket channel.

Wraps the same interview_session_service functions the REST routes use
(start_session/get_live_state/submit_answer) - no interview logic lives
here, only transport. Two rules keep this channel from reintroducing the
in-memory-only state Phase 4b was built to eliminate:

1. Every operation opens a fresh app.db.SessionLocal() and closes it
   immediately after - never Depends(get_db), which would bind one session
   to the whole connection's lifetime. The connection itself only ever
   holds transport bookkeeping (user id, session id from the URL), never a
   question/score/difficulty value that isn't re-derived from Redis/Postgres
   on the next operation. There is deliberately no "server restarted" code
   path: from the client's perspective a restart and a network blip are the
   same observed event (the connection closes), handled by the same
   reconnect-then-get_live_state flow either way.
2. All service/DB calls are synchronous and can block for seconds (LLM call,
   DB round trips). FastAPI dispatches sync *REST* route functions to a
   threadpool automatically, but that does not apply to async WebSocket
   handlers - calling them directly here would freeze the event loop for
   every other concurrent connection on this worker. So every blocking call
   is wrapped in a small sync helper run via asyncio.to_thread(); only
   websocket.accept()/receive_json()/send_json()/close() run on the loop.
"""

import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import db as db_module
from app.api.interview_sessions import _build_summary, _question_out
from app.core.config import settings
from app.core.deps import get_arq_pool
from app.core.security import decode_access_token
from app.models import User
from app.repositories import interview_plan_repository, interview_session_repository, user_repository
from app.schemas.interview_session import InterviewSessionQuestionOut, InterviewSessionStateOut, InterviewTurnEvaluationOut
from app.services import interview_session_service
from app.services.interview_session_service import InterviewSessionAbandonedError, InterviewSessionCompleteError

router = APIRouter()


class _WSUnauthorized(Exception):
    pass


class _WSSessionNotFound(Exception):
    pass


def _resolve_user(token: str, session_id: uuid.UUID) -> User:
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise _WSUnauthorized()
        user_id = uuid.UUID(payload["sub"])
    except _WSUnauthorized:
        raise
    except Exception as exc:
        raise _WSUnauthorized() from exc

    db = db_module.SessionLocal()
    try:
        user = user_repository.get_by_id(db, user_id)
        if user is None:
            raise _WSUnauthorized()
        session = interview_session_repository.get_by_id_for_user(db, session_id, user_id)
        if session is None:
            raise _WSSessionNotFound()
        return user
    finally:
        db.close()


def _state_envelope(session, live_state: dict) -> dict:
    current_question = live_state["current_question"]
    payload = InterviewSessionStateOut(
        session_id=session.id,
        interview_plan_id=session.interview_plan_id,
        status=live_state["status"],
        turn_index=live_state["turn_index"],
        total_questions=live_state["total_questions"],
        topic_number=live_state["topic_number"],
        current_difficulty=live_state["current_difficulty"],
        current_question=(
            InterviewSessionQuestionOut(
                turn_index=current_question["turn_index"],
                topic=current_question["topic"],
                difficulty=current_question["difficulty"],
                question_text=current_question["question_text"],
                topic_number=live_state["topic_number"],
                is_followup=current_question["is_followup"],
                followup_number=(
                    current_question["followup_count"] if current_question["is_followup"] else None
                ),
            )
            if current_question is not None
            else None
        ),
        last_activity_at=live_state["last_activity_at"],
        total_cost_usd=live_state["total_cost_usd"],
        cost_cap_usd=live_state["cost_cap_usd"],
        stop_reason=live_state["stop_reason"],
    ).model_dump(mode="json")
    message = {"type": "state", **payload, "summary": None}
    if live_state["status"] == "complete":
        message["summary"] = _build_summary(session).model_dump(mode="json")
    return message


def _initial_state_message(session_id: uuid.UUID, user_id: uuid.UUID) -> tuple[dict, bool]:
    db = db_module.SessionLocal()
    try:
        session = interview_session_repository.get_by_id_for_user(db, session_id, user_id)
        live_state = interview_session_service.get_live_state(db, session)
        message = _state_envelope(session, live_state)
    finally:
        db.close()
    return message, live_state["status"] in ("complete", "abandoned")


def _handle_answer(session_id: uuid.UUID, user_id: uuid.UUID, answer_text: str) -> tuple[dict, bool]:
    db = db_module.SessionLocal()
    try:
        session = interview_session_repository.get_by_id_for_user(db, session_id, user_id)
        plan = interview_plan_repository.get_by_id_for_user(db, session.interview_plan_id, user_id)
        current_turn = next((t for t in session.turns if t.idx == session.current_turn_index), None)
        if current_turn is None:
            return {"type": "error", "code": "inconsistent_state", "detail": "no current turn"}, False

        session, evaluated_turn, next_turn = interview_session_service.submit_answer(
            db, session=session, plan=plan, current_turn=current_turn, answer_text=answer_text
        )
        evaluation = InterviewTurnEvaluationOut(
            technical_score=evaluated_turn.technical_score,
            communication_score=evaluated_turn.communication_score,
            completeness_score=evaluated_turn.completeness_score,
            rationale=evaluated_turn.rationale,
        ).model_dump(mode="json")

        if next_turn is None:
            message = {
                "type": "answer_result",
                "evaluation": evaluation,
                "status": "complete",
                "next_question": None,
                "summary": _build_summary(session).model_dump(mode="json"),
                "total_cost_usd": session.total_cost_usd,
                "cost_cap_usd": session.cost_cap_usd,
                "topic_number": session.topic_number,
                "stop_reason": session.stop_reason,
            }
            return message, True

        message = {
            "type": "answer_result",
            "evaluation": evaluation,
            "status": "in_progress",
            "next_question": _question_out(next_turn).model_dump(mode="json"),
            "summary": None,
            "total_cost_usd": session.total_cost_usd,
            "cost_cap_usd": session.cost_cap_usd,
            "topic_number": session.topic_number,
            "stop_reason": session.stop_reason,
        }
        return message, False
    except InterviewSessionCompleteError:
        return {"type": "error", "code": "already_complete", "detail": "Interview session is already complete"}, True
    except InterviewSessionAbandonedError:
        return {
            "type": "error",
            "code": "abandoned",
            "detail": "Interview session was abandoned due to inactivity",
        }, True
    except ValueError as exc:
        return {"type": "error", "code": "llm_error", "detail": f"LLM returned an unusable response: {exc}"}, False
    finally:
        db.close()


def _handle_clarify(session_id: uuid.UUID, user_id: uuid.UUID, question: str) -> dict:
    db = db_module.SessionLocal()
    try:
        session = interview_session_repository.get_by_id_for_user(db, session_id, user_id)
        result = interview_session_service.handle_clarification(db, session=session, question=question)
        return {
            "type": "clarification_result",
            "question": question,
            "clarification_text": result["clarification_text"],
            "clarifications_used": result["clarifications_used"],
            "clarifications_remaining": result["clarifications_remaining"],
            "declined": result["declined"],
        }
    except InterviewSessionCompleteError:
        return {"type": "error", "code": "already_complete", "detail": "Interview session is already complete"}
    except InterviewSessionAbandonedError:
        return {
            "type": "error",
            "code": "abandoned",
            "detail": "Interview session was abandoned due to inactivity",
        }
    except ValueError as exc:
        return {"type": "error", "code": "llm_error", "detail": f"LLM returned an unusable response: {exc}"}
    finally:
        db.close()


@router.websocket("/ws/interview-sessions/{session_id}")
async def interview_session_ws(websocket: WebSocket, session_id: uuid.UUID) -> None:
    await websocket.accept()

    try:
        raw = await asyncio.wait_for(websocket.receive_json(), timeout=settings.ws_auth_timeout_seconds)
    except (TimeoutError, WebSocketDisconnect, ValueError):
        await websocket.close(code=4401)
        return

    if raw.get("type") != "auth" or not isinstance(raw.get("token"), str):
        await websocket.close(code=4401)
        return

    try:
        user = await asyncio.to_thread(_resolve_user, raw["token"], session_id)
    except _WSUnauthorized:
        await websocket.close(code=4401)
        return
    except _WSSessionNotFound:
        await websocket.close(code=4404)
        return

    message, terminal = await asyncio.to_thread(_initial_state_message, session_id, user.id)
    await websocket.send_json(message)
    if terminal:
        await websocket.close(code=1000)
        return

    while True:
        try:
            raw = await websocket.receive_json()
        except WebSocketDisconnect:
            return
        except ValueError:
            await websocket.send_json({"type": "error", "code": "bad_request", "detail": "invalid JSON"})
            continue

        if raw.get("type") == "clarify" and isinstance(raw.get("question"), str):
            message = await asyncio.to_thread(_handle_clarify, session_id, user.id, raw["question"])
            await websocket.send_json(message)
            continue

        if raw.get("type") != "answer" or not isinstance(raw.get("answer_text"), str):
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "bad_request",
                    "detail": "expected {type: 'answer', answer_text} or {type: 'clarify', question}",
                }
            )
            continue

        message, close_after = await asyncio.to_thread(_handle_answer, session_id, user.id, raw["answer_text"])
        await websocket.send_json(message)
        if message.get("status") == "complete":
            # Roadmap generation makes an LLM call + vector search, so it
            # runs as a background job (see mentor_service.py) rather than
            # inline here. Enqueueing is fast async I/O, unlike the
            # blocking work to_thread() exists to isolate above, so it's
            # fine to await directly on the event loop.
            arq_pool = await get_arq_pool()
            await arq_pool.enqueue_job("generate_roadmap", str(session_id))
        if close_after:
            await websocket.close(code=1000)
            return
