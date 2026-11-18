"""S3-compatible object storage helpers (MinIO locally)."""

from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from exaktiv_core.settings import Settings


def s3_client(s: Settings) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint,
        aws_access_key_id=s.minio_access_key.get_secret_value(),
        aws_secret_access_key=s.minio_secret_key.get_secret_value(),
        region_name="us-east-1",
        config=Config(
            connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}, signature_version="s3v4"
        ),
    )


def ensure_bucket(client: Any, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)
