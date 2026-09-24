"""Environment-driven configuration for MinIO / S3-compatible storage."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str | None = None) -> str:
    value = os.environ.get(key, default)
    if value is None or value == "":
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


def _env_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class StorageSettings:
    """Connection settings for the local MinIO data-lake bucket."""

    endpoint_url: str
    access_key: str
    secret_key: str
    bucket: str
    region: str = "us-east-1"
    use_ssl: bool = False
    max_retries: int = 5

    @classmethod
    def from_env(cls) -> StorageSettings:
        """Load settings from process environment (see ``.env.example``)."""
        return cls(
            endpoint_url=_env("MINIO_ENDPOINT_URL", "http://localhost:9006"),
            access_key=_env("MINIO_ROOT_USER", "minioadmin"),
            secret_key=_env("MINIO_ROOT_PASSWORD", "minioadmin"),
            bucket=_env("MINIO_BUCKET", "datalake-raw"),
            region=_env("MINIO_REGION", "us-east-1"),
            use_ssl=_env_bool("MINIO_USE_SSL", False),
            max_retries=int(os.environ.get("MINIO_MAX_RETRIES", "5")),
        )
