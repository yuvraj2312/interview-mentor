import uuid

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_arq_pool, get_current_user
from app.db import get_db
from app.models import InterviewPlan, InterviewSession, InterviewTurn, User
from app.repositories import interview_plan_repository, interview_session_repository
from app.schemas.interview_session import (
    CreateInterviewSessionRequest,
    InterviewSessionListItemOut,
    InterviewSessionQuestionOut,
    InterviewSessionStateOut,
    InterviewSessionSummaryOut,
    InterviewSessionTranscript,
    InterviewTurnEvaluationOut,
    InterviewTurnOut,
    StartInterviewSessionResponse,
    SubmitInterviewAnswerRequest,
    SubmitInterviewAnswerResponse,
)
from app.services import interview_session_service
from app.services.interview_session_service import (
    InterviewSessionAbandonedError,
    InterviewSessionCompleteError,
)

router = APIRouter()


def _get_session_or_404(db: DBSession, session_id: uuid.UUID, user_id: uuid.UUID) -> InterviewSession:
    session = interview_session_repository.get_by_id_for_user(db, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


def _get_plan_or_404(db: DBSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> InterviewPlan:
    plan = interview_plan_repository.get_by_id_for_user(db, plan_id, user_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Interview plan not found")
    return plan


def _question_out(turn: InterviewTurn) -> InterviewSessionQuestionOut:
    return InterviewSessionQuestionOut(
        turn_index=turn.idx, topic=turn.topic, difficulty=turn.difficulty, question_text=turn.question_text
    )


def _build_summary(session: InterviewSession) -> InterviewSessionSummaryOut:
    turns = session.turns
    n = len(turns)
    return InterviewSessionSummaryOut(
        avg_technical_score=sum(t.technical_score for t in turns) / n,
        avg_communication_score=sum(t.communication_score for t in turns) / n,
        avg_completeness_score=sum(t.completeness_score for t in turns) / n,
        difficulty_path=[t.difficulty for t in turns],
    )


def _to_list_item(session: InterviewSession) -> InterviewSessionListItemOut:
    evaluated = [t for t in session.turns if t.technical_score is not None]
    n = len(evaluated)
    return InterviewSessionListItemOut(
        session_id=session.id,
        status=session.status,
        total_questions=session.total_questions,
        turns_completed=n,
        avg_technical_score=(sum(t.technical_score for t in evaluated) / n) if n else None,
        avg_communication_score=(sum(t.communication_score for t in evaluated) / n) if n else None,
        avg_completeness_score=(sum(t.completeness_score for t in evaluated) / n) if n else None,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("", response_model=list[InterviewSessionListItemOut])
def list_interview_sessions(
    limit: int = Query(50, ge=1, le=200),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InterviewSessionListItemOut]:
    sessions = interview_session_repository.list_for_user(db, current_user.id, limit=limit)
    return [_to_list_item(s) for s in sessions]


@router.post("", response_model=StartInterviewSessionResponse)
def start_interview_session(
    payload: CreateInterviewSessionRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StartInterviewSessionResponse:
    plan = _get_plan_or_404(db, payload.interview_plan_id, current_user.id)
    if plan.status != "ready":
        raise HTTPException(status_code=400, detail="Interview plan is not ready")

    try:
        session, first_turn = interview_session_service.start_session(db, user_id=current_user.id, plan=plan)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc

    return StartInterviewSessionResponse(
        session_id=session.id, total_questions=session.total_questions, question=_question_out(first_turn)
    )


@router.post("/{session_id}/answer", response_model=SubmitInterviewAnswerResponse)
async def submit_interview_answer(
    session_id: uuid.UUID,
    payload: SubmitInterviewAnswerRequest,
    db: DBSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    current_user: User = Depends(get_current_user),
) -> SubmitInterviewAnswerResponse:
    session = _get_session_or_404(db, session_id, current_user.id)

    plan = _get_plan_or_404(db, session.interview_plan_id, current_user.id)
    current_turn = next((t for t in session.turns if t.idx == session.current_turn_index), None)
    if current_turn is None:
        raise HTTPException(status_code=500, detail="Session state is inconsistent: no current turn")

    try:
        session, evaluated_turn, next_turn = interview_session_service.submit_answer(
            db, session=session, plan=plan, current_turn=current_turn, answer_text=payload.answer_text
        )
    except InterviewSessionCompleteError as exc:
        raise HTTPException(status_code=400, detail="Interview session is already complete") from exc
    except InterviewSessionAbandonedError as exc:
        raise HTTPException(status_code=409, detail="Interview session was abandoned due to inactivity") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc

    evaluation_out = InterviewTurnEvaluationOut(
        technical_score=evaluated_turn.technical_score,
        communication_score=evaluated_turn.communication_score,
        completeness_score=evaluated_turn.completeness_score,
        rationale=evaluated_turn.rationale,
    )

    if next_turn is None:
        # Roadmap generation makes an LLM call + vector search, so like
        # resume/JD analysis it runs as a background job rather than
        # inline in this response (see mentor_service.py).
        await arq_pool.enqueue_job("generate_roadmap", str(session.id))
        return SubmitInterviewAnswerResponse(
            evaluation=evaluation_out,
            status="complete",
            summary=_build_summary(session),
            total_cost_usd=session.total_cost_usd,
            cost_cap_usd=session.cost_cap_usd,
            stop_reason=session.stop_reason,
        )

    return SubmitInterviewAnswerResponse(
        evaluation=evaluation_out,
        status="in_progress",
        next_question=_question_out(next_turn),
        total_cost_usd=session.total_cost_usd,
        cost_cap_usd=session.cost_cap_usd,
        stop_reason=session.stop_reason,
    )


@router.get("/{session_id}", response_model=InterviewSessionTranscript)
def get_interview_session(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewSessionTranscript:
    session = _get_session_or_404(db, session_id, current_user.id)

    turns = [
        InterviewTurnOut(
            turn_index=t.idx,
            topic=t.topic,
            difficulty=t.difficulty,
            question_text=t.question_text,
            answer_text=t.answer_text,
            evaluation=(
                InterviewTurnEvaluationOut(
                    technical_score=t.technical_score,
                    communication_score=t.communication_score,
                    completeness_score=t.completeness_score,
                    rationale=t.rationale,
                )
                if t.answer_text is not None
                else None
            ),
        )
        for t in session.turns
    ]

    return InterviewSessionTranscript(
        session_id=session.id, status=session.status, total_questions=session.total_questions, turns=turns
    )


@router.get("/{session_id}/state", response_model=InterviewSessionStateOut)
def get_interview_session_state(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewSessionStateOut:
    session = _get_session_or_404(db, session_id, current_user.id)
    live_state = interview_session_service.get_live_state(db, session)

    return InterviewSessionStateOut(
        session_id=session.id,
        interview_plan_id=session.interview_plan_id,
        status=live_state["status"],
        turn_index=live_state["turn_index"],
        total_questions=live_state["total_questions"],
        current_difficulty=live_state["current_difficulty"],
        current_question=(
            InterviewSessionQuestionOut(**live_state["current_question"])
            if live_state["current_question"] is not None
            else None
        ),
        last_activity_at=live_state["last_activity_at"],
        total_cost_usd=live_state["total_cost_usd"],
        cost_cap_usd=live_state["cost_cap_usd"],
        stop_reason=live_state["stop_reason"],
    )
