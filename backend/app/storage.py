"""Object storage client (S3-compatible, MinIO in dev).

Original resume files never go in Postgres - only storage_key metadata
is relational (CLAUDE.md: resume files never go in PostgreSQL). boto3's
S3 API is already the swap-a-provider abstraction here, so no parallel
adapter class is needed the way llm_adapter.py wraps the LLM provider.
"""

import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

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
    # Uses head_bucket, not list_buckets: list_buckets is an account-level S3
    # operation that a bucket-scoped R2 API token (Object Read & Write on a
    # single bucket, the recommended least-privilege setup) is not permitted
    # to call, and fails with AccessDenied even though the token is otherwise
    # valid. head_bucket only needs permission on this one bucket, so it
    # works with a scoped token. A scoped R2 token is created against an
    # existing bucket, so create_bucket below is mainly for local MinIO dev,
    # where the bucket may not exist yet.
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=settings.minio_bucket_name)
        else:
            raise


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
