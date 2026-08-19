"""Object storage client (S3-compatible, MinIO in dev).

Original resume files never go in Postgres - only storage_key metadata
is relational (CLAUDE.md: resume files never go in PostgreSQL). boto3's
S3 API is already the swap-a-provider abstraction here, so no parallel
adapter class is needed the way llm_adapter.py wraps the LLM provider.
"""

import uuid

import boto3
from botocore.client import Config

from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        use_ssl=settings.minio_secure,
    )


def ensure_bucket_exists() -> None:
    client = get_s3_client()
    existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
    if settings.minio_bucket_name not in existing:
        client.create_bucket(Bucket=settings.minio_bucket_name)


def build_resume_object_key(user_id: uuid.UUID, resume_id: uuid.UUID, filename: str) -> str:
    return f"resumes/{user_id}/{resume_id}/{filename}"


def upload_resume_file(file_bytes: bytes, key: str, content_type: str) -> None:
    client = get_s3_client()
    client.put_object(
        Bucket=settings.minio_bucket_name,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )


def download_resume_file(key: str) -> bytes:
    client = get_s3_client()
    response = client.get_object(Bucket=settings.minio_bucket_name, Key=key)
    return response["Body"].read()
