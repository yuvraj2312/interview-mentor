from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Drives production-only validation below (CORS today) - not a general
    # feature-flag mechanism, so don't sprinkle `if environment == ...`
    # checks elsewhere without good reason.
    environment: Literal["development", "production"] = "development"

    database_url: str
    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # Absolute ceiling on a single login session, independent of activity or
    # refresh-token rotation (rotation alone would let a continuously-active
    # session, or a leaked refresh token kept alive by repeated use, extend
    # forever - see auth_service.refresh()'s session_started_at check). 24h
    # ("re-authenticate once per calendar day") follows OWASP session-timeout
    # guidance for a moderate-sensitivity app (candidate PII, no payment/health
    # data): short enough to bound exposure from a leaked token, long enough
    # not to interrupt someone doing multiple prep sessions in a day. The
    # separate idle timeout (frontend) handles the "abandoned tab" case well
    # before this ever matters for a legitimate user.
    absolute_session_max_hours: int = 24

    # Dev-only default: covers Vite's auto-incremented port when 5173 is
    # already taken, without needing a .env override for local dev. This
    # default is never used in production - see _validate_production_cors,
    # which requires CORS_ORIGINS to be set explicitly there instead.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]

    redis_url: str = "redis://localhost:6380/0"
    redis_key_prefix: str = "interview_mentor"
    interview_session_inactivity_timeout_seconds: int = 900
    interview_session_state_ttl_seconds: int = 86400
    interview_session_stuck_transient_seconds: int = 120
    ws_auth_timeout_seconds: float = 10.0
    interview_session_max_cost_usd: float = 0.5

    minio_endpoint_url: str = "http://localhost:9000"
    # No fallback, deliberately - "minioadmin"/"minioadmin" is a real,
    # well-known default credential, not a placeholder, so it must come from
    # the environment same as jwt_secret_key/anthropic_api_key. Local dev
    # still works unchanged since backend/.env.example sets both explicitly.
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_name: str = "resumes"
    minio_secure: bool = False

    qdrant_url: str = "http://localhost:6333"
    qdrant_learning_resources_collection: str = "learning_resources"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    skill_match_similarity_threshold: float = 0.85
    # Cost-control tripwire only, NOT a confidence boundary like the
    # threshold above - calibration (see skill_gap_service.py's
    # _llm_fallback_pass docstring) found cosine similarity in this range
    # is not separable between "unrelated" and "same skill, different
    # words" for short professional-skill phrases (a real synonym pair can
    # score lower than a maximally-unrelated pair). Set low so it
    # essentially never excludes a real match; the LLM fallback layer does
    # the actual discrimination for everything above it.
    skill_match_ambiguous_floor: float = 0.35
    skill_trend_delta_threshold: float = 0.5
    # 0.6, not the original 0.3 (2026-09-13 investigation into
    # "Continuous Delivery"/"RESTful Web APIs" being over-recommended
    # across unrelated roadmap items): the 10-resource seed KB
    # (learning_resources_seed.py) has zero non-tech-domain coverage, and at
    # 0.3 an out-of-domain query still always returned its "least-bad" 3
    # hits instead of correctly returning few/none - those hub-like
    # resources (highest average cosine similarity across a diverse set of
    # real queries, confirmed by direct embedding computation) then won a
    # disproportionate share of every roadmap's resource slots. Threshold
    # is data-justified, not guessed: across 21 real roadmap items, every
    # genuinely-relevant match's top score was >= 0.634, while every
    # confirmed-irrelevant out-of-domain match scored <= 0.576 - 0.6 sits
    # cleanly in that gap.
    learning_resource_similarity_threshold: float = 0.6

    # Rate limits on auth endpoints (see app.core.rate_limit), expressed as
    # "N/minute" strings for slowapi. Defaults are the numbers justified in
    # docs/deployment.md; override per-environment only if real usage shows
    # they're wrong, not speculatively.
    rate_limit_login: str = "10/minute"
    rate_limit_signup: str = "5/minute"
    rate_limit_refresh: str = "20/minute"

    # Sentry is fully inert until this is set (see app.main) - no DSN, no
    # sentry_sdk.init() call at all, not just a disabled client.
    sentry_dsn: str | None = None

    # Used only by scripts/backup_db.py, not the running app. Reuses the
    # existing MinIO/S3-compatible credentials (minio_access_key etc.) since
    # in production those already point at real object storage - a separate
    # bucket/prefix just keeps backups out of the resumes bucket.
    backup_s3_bucket: str | None = None
    backup_retention_days: int = 7

    # Matches the frontend's existing upload hint (ResumeStep.tsx's
    # FileDropzone already says "up to 10MB") - real resumes, even
    # multi-page PDFs with an embedded photo, are almost always a few MB at
    # most. 10MB gives headroom while still bounding the worst case. Note
    # (see app/api/resumes.py) this check runs after the file is already
    # fully received - FastAPI/Starlette buffer the whole multipart body
    # before the endpoint function runs at all, so this bounds what gets
    # stored, not what gets received.
    resume_max_upload_bytes: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def _validate_production_cors(self) -> "Settings":
        if self.environment != "production":
            return self

        if not self.cors_origins:
            raise ValueError(
                "CORS_ORIGINS must be set explicitly when ENVIRONMENT=production "
                "(no dev default is used in production)."
            )
        for origin in self.cors_origins:
            if origin.strip() == "*":
                raise ValueError("CORS_ORIGINS must not contain a wildcard '*' in production.")
            lowered = origin.lower()
            if "localhost" in lowered or "127.0.0.1" in lowered:
                raise ValueError(
                    f"CORS_ORIGINS must not contain a localhost origin in production: {origin!r}"
                )
        return self

    @model_validator(mode="after")
    def _validate_production_hosts(self) -> "Settings":
        # Guards one direction (production silently pointed at a forgotten
        # local DB/Redis) - the other direction (local dev accidentally
        # pointed at the real production DB) can't be caught by a validator
        # since that URL looks legitimate from development too; that's what
        # the startup log line in app/main.py is for instead
        # (docs/deployment.md's environment separation section).
        if self.environment != "production":
            return self

        for name, url in (("DATABASE_URL", self.database_url), ("REDIS_URL", self.redis_url)):
            lowered = url.lower()
            if "localhost" in lowered or "127.0.0.1" in lowered:
                raise ValueError(f"{name} must not point at localhost in production: {url!r}")
        return self


settings = Settings()
