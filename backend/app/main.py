import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import (
    auth,
    health,
    interview_plans,
    interview_sessions,
    job_descriptions,
    resumes,
    roadmap,
    sessions,
    skill_gap,
    skill_profiles,
)
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter
from app.embedding_adapter import warm_embedding_model
from app.services import vector_store_service
from app.storage import ensure_bucket_exists
from app.websockets import interview_session_ws

configure_logging()

logger = logging.getLogger("app.main")
# Deliberately logs only hostname/dbname (via urlparse), never
# username/password - a misconfigured environment (e.g. local dev pointed at
# the production DB, or vice versa) becomes visible in every boot's logs
# instead of silently running against the wrong thing (docs/deployment.md's
# environment separation section).
_db_url = urlparse(settings.database_url)
_redis_url = urlparse(settings.redis_url)
logger.info(
    "startup environment=%s database=%s/%s redis=%s",
    settings.environment,
    _db_url.hostname,
    (_db_url.path or "").lstrip("/"),
    _redis_url.hostname,
)

if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket_exists()
    warm_embedding_model()
    vector_store_service.ensure_collection(
        settings.qdrant_learning_resources_collection, vector_size=settings.embedding_dimension
    )
    yield


app = FastAPI(title="Interview Mentor", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(job_descriptions.router, prefix="/job-descriptions", tags=["job-descriptions"])
app.include_router(skill_gap.router, prefix="/skill-gap", tags=["skill-gap"])
app.include_router(skill_profiles.router, prefix="/skill-profile", tags=["skill-profile"])
app.include_router(interview_plans.router, prefix="/interview-plans", tags=["interview-plans"])
app.include_router(interview_sessions.router, prefix="/interview-sessions", tags=["interview-sessions"])
app.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
app.include_router(interview_session_ws.router, tags=["interview-sessions-ws"])
