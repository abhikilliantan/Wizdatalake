"""Storage package — S3-compatible MinIO client for the raw data lake."""

from __future__ import annotations

from typing import TYPE_CHECKING

from storage.exceptions import StorageError, StorageUploadError
from storage.partitioning import build_partition_prefix

if TYPE_CHECKING:
    from storage.client import ObjectStorage
    from storage.config import StorageSettings

__all__ = [
    "ObjectStorage",
    "StorageSettings",
    "StorageError",
    "StorageUploadError",
    "build_partition_prefix",
]


def __getattr__(name: str):
    """Lazy-load heavy modules (boto3) so lightweight helpers stay importable."""
    if name == "ObjectStorage":
        from storage.client import ObjectStorage

        return ObjectStorage
    if name == "StorageSettings":
        from storage.config import StorageSettings

        return StorageSettings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
