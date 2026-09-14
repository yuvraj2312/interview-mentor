import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE_KWARGS = dict(
    _env_file=None,
    database_url="postgresql+psycopg2://u:p@localhost:5433/db",
    anthropic_api_key="test-key",
    jwt_secret_key="test-secret",
    minio_access_key="test-access",
    minio_secret_key="test-secret-key",
)


def test_development_allows_localhost_cors_default():
    settings = Settings(**BASE_KWARGS)
    assert settings.environment == "development"
    assert any("localhost" in origin for origin in settings.cors_origins)


def test_production_requires_cors_origins_to_be_set():
    with pytest.raises(ValidationError, match="must be set explicitly"):
        Settings(**BASE_KWARGS, environment="production", cors_origins=[])


def test_production_rejects_localhost_origin():
    with pytest.raises(ValidationError, match="localhost"):
        Settings(**BASE_KWARGS, environment="production", cors_origins=["http://localhost:5173"])


def test_production_rejects_wildcard_origin():
    with pytest.raises(ValidationError, match="wildcard"):
        Settings(**BASE_KWARGS, environment="production", cors_origins=["*"])


def test_production_accepts_real_origin():
    settings = Settings(
        **{**BASE_KWARGS, "database_url": "postgresql+psycopg2://u:p@prod-db.example.com:5432/db"},
        environment="production",
        cors_origins=["https://interviewmentor.app"],
        redis_url="redis://prod-redis.example.com:6379/0",
    )
    assert settings.cors_origins == ["https://interviewmentor.app"]


def test_production_rejects_localhost_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL.*localhost"):
        Settings(
            **BASE_KWARGS,
            environment="production",
            cors_origins=["https://interviewmentor.app"],
            redis_url="redis://prod-redis.example.com:6379/0",
        )


def test_production_rejects_localhost_redis_url():
    with pytest.raises(ValidationError, match="REDIS_URL.*localhost"):
        Settings(
            **{**BASE_KWARGS, "database_url": "postgresql+psycopg2://u:p@prod-db.example.com:5432/db"},
            environment="production",
            cors_origins=["https://interviewmentor.app"],
        )


def test_minio_credentials_have_no_hardcoded_fallback():
    # The point is that nothing in *code* supplies a fallback - _env_file is
    # already disabled via BASE_KWARGS, so omitting the minio_* kwargs here
    # means they truly have nothing to fall back to.
    kwargs = {k: v for k, v in BASE_KWARGS.items() if k not in ("minio_access_key", "minio_secret_key")}
    with pytest.raises(ValidationError):
        Settings(**kwargs)
