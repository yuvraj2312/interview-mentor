import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Answer, Evaluation, User
from app.models import Question as QuestionModel
from app.models import Session as SessionModel
from app.repositories import session_repository
from app.schemas.interview import (
    EvaluationOut,
    QuestionOut,
    SessionTranscript,
    StartSessionRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SummaryOut,
    TranscriptTurn,
)
from app.services import interview_service

router = APIRouter()


def _get_session_or_404(db: DBSession, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel:
    session = session_repository.get_by_id_for_user(db, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=StartSessionResponse)
def start_session(
    payload: StartSessionRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StartSessionResponse:
    try:
        generated = interview_service.generate_questions(db, payload.resume_text, payload.jd_text)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc

    session = session_repository.create(
        db, user_id=current_user.id, resume_text=payload.resume_text, jd_text=payload.jd_text
    )

    questions = [
        QuestionModel(
            session_id=session.id,
            idx=i,
            text=q["question"],
            topic=q["topic"],
            difficulty=q["difficulty"],
        )
        for i, q in enumerate(generated)
    ]
    db.add_all(questions)
    db.commit()

    first = questions[0]
    return StartSessionResponse(
        session_id=session.id,
        question_number=1,
        total_questions=len(questions),
        question=QuestionOut(id=first.id, text=first.text, topic=first.topic, difficulty=first.difficulty),
    )


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
def submit_answer(
    session_id: uuid.UUID,
    payload: SubmitAnswerRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmitAnswerResponse:
    session = _get_session_or_404(db, session_id, current_user.id)
    if session.status == "complete":
        raise HTTPException(status_code=400, detail="Session is already complete")

    current_question = next((q for q in session.questions if q.idx == session.current_index), None)
    if current_question is None:
        raise HTTPException(status_code=500, detail="Session state is inconsistent: no current question")

    try:
        result = interview_service.evaluate_answer(db, current_question.text, payload.answer_text)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned an unusable response: {exc}") from exc

    answer = Answer(question_id=current_question.id, text=payload.answer_text)
    db.add(answer)
    db.flush()

    evaluation = Evaluation(
        answer_id=answer.id,
        technical_score=result["technical_score"],
        communication_score=result["communication_score"],
        completeness_score=result["completeness_score"],
        rationale=result["rationale"],
    )
    db.add(evaluation)

    session.current_index += 1
    evaluation_out = EvaluationOut(
        technical_score=evaluation.technical_score,
        communication_score=evaluation.communication_score,
        completeness_score=evaluation.completeness_score,
        rationale=evaluation.rationale,
    )

    if session.current_index >= len(session.questions):
        session.status = "complete"
        db.commit()

        evaluations = (
            db.query(Evaluation)
            .join(Answer)
            .join(QuestionModel)
            .filter(QuestionModel.session_id == session.id)
            .all()
        )
        n = len(evaluations)
        summary = SummaryOut(
            avg_technical_score=sum(e.technical_score for e in evaluations) / n,
            avg_communication_score=sum(e.communication_score for e in evaluations) / n,
            avg_completeness_score=sum(e.completeness_score for e in evaluations) / n,
        )
        return SubmitAnswerResponse(evaluation=evaluation_out, status="complete", summary=summary)

    db.commit()
    next_question = next(q for q in session.questions if q.idx == session.current_index)
    return SubmitAnswerResponse(
        evaluation=evaluation_out,
        status="in_progress",
        question_number=session.current_index + 1,
        total_questions=len(session.questions),
        next_question=QuestionOut(
            id=next_question.id,
            text=next_question.text,
            topic=next_question.topic,
            difficulty=next_question.difficulty,
        ),
    )


@router.get("/{session_id}", response_model=SessionTranscript)
def get_session(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionTranscript:
    session = _get_session_or_404(db, session_id, current_user.id)

    turns = [
        TranscriptTurn(
            question=QuestionOut(id=q.id, text=q.text, topic=q.topic, difficulty=q.difficulty),
            answer_text=q.answer.text if q.answer else None,
            evaluation=(
                EvaluationOut(
                    technical_score=q.answer.evaluation.technical_score,
                    communication_score=q.answer.evaluation.communication_score,
                    completeness_score=q.answer.evaluation.completeness_score,
                    rationale=q.answer.evaluation.rationale,
                )
                if q.answer and q.answer.evaluation
                else None
            ),
        )
        for q in session.questions
    ]

    return SessionTranscript(
        session_id=session.id,
        status=session.status,
        resume_text=session.resume_text,
        jd_text=session.jd_text,
        turns=turns,
    )
