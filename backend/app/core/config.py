from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = ["http://localhost:5173"]

    redis_url: str = "redis://localhost:6380/0"
    redis_key_prefix: str = "interview_mentor"
    interview_session_inactivity_timeout_seconds: int = 900
    interview_session_state_ttl_seconds: int = 86400
    interview_session_stuck_transient_seconds: int = 120
    ws_auth_timeout_seconds: float = 10.0
    interview_session_max_cost_usd: float = 2.0

    minio_endpoint_url: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "resumes"
    minio_secure: bool = False

    qdrant_url: str = "http://localhost:6333"
    qdrant_learning_resources_collection: str = "learning_resources"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    skill_match_similarity_threshold: float = 0.85
    skill_trend_delta_threshold: float = 0.5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
