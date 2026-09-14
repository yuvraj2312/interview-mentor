"""Scheduled Postgres backup: pg_dump -> gzip-free custom format -> S3-compatible bucket.

Not run by the app itself - invoke this on a schedule (cron, or your host's
scheduled-job feature). See docs/deployment.md for setup and for when to
prefer your Postgres host's own built-in automated backups instead.

Usage:
    python scripts/backup_db.py

Requires BACKUP_S3_BUCKET to be set (see app.core.config); reuses the same
MinIO/S3 credentials as the app (MINIO_ACCESS_KEY/MINIO_SECRET_KEY/
MINIO_ENDPOINT_URL) since in production those already point at real object
storage.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings
from app.storage import get_s3_client

BACKUP_PREFIX = "db-backups/"


def _pg_dump_url(database_url: str) -> str:
    # SQLAlchemy's "postgresql+psycopg2://" scheme isn't understood by the
    # pg_dump CLI, which wants a plain "postgresql://" URL.
    parsed = urlparse(database_url)
    scheme = "postgresql"
    return parsed._replace(scheme=scheme).geturl()


def _run_pg_dump(database_url: str, output_path: Path) -> None:
    result = subprocess.run(
        ["pg_dump", _pg_dump_url(database_url), "-Fc", "-f", str(output_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed (exit {result.returncode}): {result.stderr}")


def _prune_old_backups(client, bucket: str) -> None:
    cutoff = datetime.now(timezone.utc).timestamp() - settings.backup_retention_days * 86400
    response = client.list_objects_v2(Bucket=bucket, Prefix=BACKUP_PREFIX)
    for obj in response.get("Contents", []):
        if obj["LastModified"].timestamp() < cutoff:
            client.delete_object(Bucket=bucket, Key=obj["Key"])
            print(f"Pruned old backup: {obj['Key']}")


def main() -> None:
    if not settings.backup_s3_bucket:
        print("BACKUP_S3_BUCKET is not set - refusing to run with no destination.", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"interview_mentor_{timestamp}.dump"
    output_path = Path.cwd() / filename

    try:
        print(f"Running pg_dump -> {output_path}")
        _run_pg_dump(settings.database_url, output_path)

        client = get_s3_client()
        key = f"{BACKUP_PREFIX}{filename}"
        print(f"Uploading to s3://{settings.backup_s3_bucket}/{key}")
        client.upload_file(str(output_path), settings.backup_s3_bucket, key)

        _prune_old_backups(client, settings.backup_s3_bucket)
        print("Backup complete.")
    finally:
        output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
