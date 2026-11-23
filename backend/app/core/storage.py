"""Object storage (SeaweedFS via its S3-compatible API).

Two buckets:
  * public  – non-sensitive media (article covers, learning images). Served directly via nginx.
  * private – anything about a child (photos, attachments). Only reachable through
              short-lived presigned URLs generated for an authorised user.

Presigned URLs are signed against PUBLIC_BASE_URL so the browser can use them through nginx,
which forwards the original Host header to SeaweedFS so the signature still verifies.
"""

import uuid
from functools import lru_cache
from pathlib import PurePosixPath
from typing import BinaryIO, Literal

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.core.config import settings

Visibility = Literal["public", "private"]

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _client(endpoint_url: str) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


@lru_cache
def internal_client() -> BaseClient:
    """Client used by the backend to talk to SeaweedFS inside the Docker network."""
    return _client(settings.s3_endpoint_url)


@lru_cache
def public_signing_client() -> BaseClient:
    """Client used only to sign URLs that the browser will open via nginx."""
    return _client(settings.public_base_url)


def bucket_for(visibility: Visibility) -> str:
    return settings.s3_bucket_public if visibility == "public" else settings.s3_bucket_private


def ensure_buckets() -> None:
    client = internal_client()
    existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
    for bucket in (settings.s3_bucket_public, settings.s3_bucket_private):
        if bucket not in existing:
            client.create_bucket(Bucket=bucket)


def upload_file(
    fileobj: BinaryIO, *, filename: str, content_type: str, visibility: Visibility, prefix: str
) -> str:
    """Upload and return the object key."""
    suffix = PurePosixPath(filename).suffix.lower()[:10]
    key = f"{prefix.strip('/')}/{uuid.uuid4().hex}{suffix}"
    internal_client().upload_fileobj(
        fileobj, bucket_for(visibility), key, ExtraArgs={"ContentType": content_type}
    )
    return key


def delete_file(key: str, visibility: Visibility) -> None:
    internal_client().delete_object(Bucket=bucket_for(visibility), Key=key)


def file_url(key: str | None, visibility: Visibility) -> str | None:
    if not key:
        return None
    if visibility == "public":
        return f"{settings.public_base_url.rstrip('/')}/{settings.s3_bucket_public}/{key}"
    return public_signing_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_private, "Key": key},
        ExpiresIn=settings.s3_presigned_expire_seconds,
    )
