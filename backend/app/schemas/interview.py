import uuid

from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    resume_text: str
    jd_text: str


class QuestionOut(BaseModel):
    id: uuid.UUID
    text: str
    topic: str
    difficulty: str


class StartSessionResponse(BaseModel):
    session_id: uuid.UUID
    question_number: int
    total_questions: int
    question: QuestionOut


class SubmitAnswerRequest(BaseModel):
    answer_text: str


class EvaluationOut(BaseModel):
    technical_score: float
    communication_score: float
    completeness_score: float
    rationale: str


class SummaryOut(BaseModel):
    avg_technical_score: float
    avg_communication_score: float
    avg_completeness_score: float


class SubmitAnswerResponse(BaseModel):
    evaluation: EvaluationOut
    status: str
    question_number: int | None = None
    total_questions: int | None = None
    next_question: QuestionOut | None = None
    summary: SummaryOut | None = None


class TranscriptTurn(BaseModel):
    question: QuestionOut
    answer_text: str | None = None
    evaluation: EvaluationOut | None = None


class SessionTranscript(BaseModel):
    session_id: uuid.UUID
    status: str
    resume_text: str
    jd_text: str
    turns: list[TranscriptTurn]
