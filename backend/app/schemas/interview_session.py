import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CreateInterviewSessionRequest(BaseModel):
    interview_plan_id: uuid.UUID


class InterviewSessionQuestionOut(BaseModel):
    turn_index: int
    topic: str
    difficulty: int
    question_text: str


class StartInterviewSessionResponse(BaseModel):
    session_id: uuid.UUID
    total_questions: int
    question: InterviewSessionQuestionOut


class SubmitInterviewAnswerRequest(BaseModel):
    answer_text: str


class InterviewTurnEvaluationOut(BaseModel):
    technical_score: float
    communication_score: float
    completeness_score: float
    rationale: str


class InterviewSessionSummaryOut(BaseModel):
    avg_technical_score: float
    avg_communication_score: float
    avg_completeness_score: float
    difficulty_path: list[int]


class SubmitInterviewAnswerResponse(BaseModel):
    evaluation: InterviewTurnEvaluationOut
    status: Literal["in_progress", "complete"]
    next_question: InterviewSessionQuestionOut | None = None
    summary: InterviewSessionSummaryOut | None = None
    total_cost_usd: float
    cost_cap_usd: float
    stop_reason: Literal["completed", "cost_cap_exceeded"] | None = None


class InterviewTurnOut(BaseModel):
    turn_index: int
    topic: str
    difficulty: int
    question_text: str
    answer_text: str | None = None
    evaluation: InterviewTurnEvaluationOut | None = None


class InterviewSessionTranscript(BaseModel):
    session_id: uuid.UUID
    status: str
    total_questions: int
    turns: list[InterviewTurnOut]


class InterviewSessionListItemOut(BaseModel):
    session_id: uuid.UUID
    status: str
    total_questions: int
    turns_completed: int
    avg_technical_score: float | None
    avg_communication_score: float | None
    avg_completeness_score: float | None
    created_at: datetime
    completed_at: datetime | None


class InterviewSessionStateOut(BaseModel):
    session_id: uuid.UUID
    interview_plan_id: uuid.UUID
    status: Literal["planned", "in_progress", "evaluating", "advancing", "complete", "abandoned"]
    turn_index: int
    total_questions: int
    current_difficulty: int
    current_question: InterviewSessionQuestionOut | None = None
    last_activity_at: datetime
    total_cost_usd: float
    cost_cap_usd: float
    stop_reason: Literal["completed", "cost_cap_exceeded"] | None = None
