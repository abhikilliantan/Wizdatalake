"""Domain exceptions for the storage layer."""

from __future__ import annotations


class StorageError(Exception):
    """Base error for all storage-layer failures."""


class StorageUploadError(StorageError):
    """Raised when an object upload to MinIO / S3 fails after retries."""
