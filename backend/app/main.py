from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, interview_plans, interview_sessions, job_descriptions, resumes, sessions, skill_gap
from app.core.config import settings
from app.websockets import interview_session_ws

app = FastAPI(title="Interview Mentor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(job_descriptions.router, prefix="/job-descriptions", tags=["job-descriptions"])
app.include_router(skill_gap.router, prefix="/skill-gap", tags=["skill-gap"])
app.include_router(interview_plans.router, prefix="/interview-plans", tags=["interview-plans"])
app.include_router(interview_sessions.router, prefix="/interview-sessions", tags=["interview-sessions"])
app.include_router(interview_session_ws.router, tags=["interview-sessions-ws"])
