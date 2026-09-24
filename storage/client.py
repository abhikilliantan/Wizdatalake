"""S3-compatible object storage backed by MinIO.

Provides partitioned writes (`/year=YYYY/month=MM/day=DD/`), metadata
tagging, and retry-aware uploads for the raw data-lake layer.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional, Union

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from storage.config import StorageSettings
from storage.exceptions import StorageError, StorageUploadError
from storage.partitioning import build_partition_prefix

logger = logging.getLogger(__name__)

BytesLike = Union[bytes, bytearray, memoryview]
JsonLike = Union[Mapping[str, Any], list[Any]]


class ObjectStorage:
    """Thin, typed wrapper around an S3-compatible (MinIO) client.

    All configuration is loaded from environment variables via
    :class:`~storage.config.StorageSettings` unless an explicit
    ``settings`` instance is supplied (useful for tests).
    """

    def __init__(
        self,
        settings: Optional[StorageSettings] = None,
        *,
        client: Optional[BaseClient] = None,
    ) -> None:
        self.settings = settings or StorageSettings.from_env()
        self._client = client or self._build_client(self.settings)
        self._ensure_bucket()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_client(settings: StorageSettings) -> BaseClient:
        """Create a boto3 S3 client pointed at the local MinIO endpoint."""
        return boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name=settings.region,
            config=Config(
                signature_version="s3v4",
                retries={
                    "max_attempts": settings.max_retries,
                    "mode": "standard",
                },
                s3={"addressing_style": "path"},
            ),
            use_ssl=settings.use_ssl,
        )

    def _ensure_bucket(self) -> None:
        """Create the target bucket if it does not already exist."""
        bucket = self.settings.bucket
        try:
            self._client.head_bucket(Bucket=bucket)
            logger.debug("Bucket already exists: %s", bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            # MinIO / S3 may return 404 or 403 when the bucket is missing
            if error_code in {"404", "NoSuchBucket", "403", "NotFound"}:
                try:
                    self._client.create_bucket(Bucket=bucket)
                    logger.info("Created bucket: %s", bucket)
                except ClientError as create_exc:
                    raise StorageError(
                        f"Failed to create bucket '{bucket}': {create_exc}"
                    ) from create_exc
            else:
                raise StorageError(
                    f"Unable to verify bucket '{bucket}': {exc}"
                ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put_bytes(
        self,
        data: BytesLike,
        *,
        source: str,
        event_type: str,
        content_type: str = "application/octet-stream",
        object_id: Optional[str] = None,
        event_time: Optional[datetime] = None,
        extra_tags: Optional[Mapping[str, str]] = None,
        extra_metadata: Optional[Mapping[str, str]] = None,
        extension: str = "bin",
    ) -> str:
        """Upload raw bytes to a Hive-style date partition.

        Returns the full object key that was written.

        Parameters
        ----------
        data:
            Payload body.
        source:
            Logical origin of the data (e.g. ``"salesforce"``, ``"hubspot"``,
            ``"app:orders"``). Stored as an object tag and path segment.
        event_type:
            Event / entity name (e.g. ``"contact.updated"``). Used in the
            object key and as a tag.
        content_type:
            MIME type of the payload.
        object_id:
            Optional stable identifier. A UUID4 is generated when omitted.
        event_time:
            Timestamp used for partitioning. Defaults to UTC now.
        extra_tags:
            Additional S3 object tags (must be short ASCII key/value pairs).
        extra_metadata:
            Additional user-defined object metadata (stored as headers).
        extension:
            File extension appended to the object key (no leading dot).
        """
        ts = event_time or datetime.now(timezone.utc)
        oid = object_id or str(uuid.uuid4())
        safe_source = _sanitize_path_segment(source)
        safe_event = _sanitize_path_segment(event_type)

        prefix = build_partition_prefix(ts, source=safe_source)
        key = f"{prefix}/{safe_event}_{oid}.{extension.lstrip('.')}"

        tags = self._build_tags(
            source=source,
            event_type=event_type,
            object_id=oid,
            event_time=ts,
            extra=extra_tags,
        )
        metadata = self._build_metadata(
            source=source,
            event_type=event_type,
            object_id=oid,
            event_time=ts,
            extra=extra_metadata,
        )

        try:
            self._client.put_object(
                Bucket=self.settings.bucket,
                Key=key,
                Body=bytes(data),
                ContentType=content_type,
                Metadata=metadata,
                Tagging=_encode_tagging(tags),
            )
        except (ClientError, BotoCoreError) as exc:
            logger.exception(
                "Upload failed bucket=%s key=%s source=%s",
                self.settings.bucket,
                key,
                source,
            )
            raise StorageUploadError(
                f"Failed to upload object to s3://{self.settings.bucket}/{key}: {exc}"
            ) from exc

        logger.info(
            "Stored object s3://%s/%s bytes=%d source=%s event_type=%s",
            self.settings.bucket,
            key,
            len(data),
            source,
            event_type,
        )
        return key

    def put_json(
        self,
        payload: JsonLike,
        *,
        source: str,
        event_type: str,
        object_id: Optional[str] = None,
        event_time: Optional[datetime] = None,
        extra_tags: Optional[Mapping[str, str]] = None,
        extra_metadata: Optional[Mapping[str, str]] = None,
    ) -> str:
        """Serialize ``payload`` as UTF-8 JSON and upload via :meth:`put_bytes`."""
        body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
        return self.put_bytes(
            body,
            source=source,
            event_type=event_type,
            content_type="application/json",
            object_id=object_id,
            event_time=event_time,
            extra_tags=extra_tags,
            extra_metadata=extra_metadata,
            extension="json",
        )

    def put_file(
        self,
        file_path: str,
        *,
        source: str,
        event_type: str = "file.upload",
        object_id: Optional[str] = None,
        event_time: Optional[datetime] = None,
        extra_tags: Optional[Mapping[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """Read a local file and upload it with partitioning + tags."""
        guessed, _ = mimetypes.guess_type(file_path)
        ctype = content_type or guessed or "application/octet-stream"
        extension = file_path.rsplit(".", 1)[-1] if "." in file_path else "bin"

        with open(file_path, "rb") as fh:
            data = fh.read()

        return self.put_bytes(
            data,
            source=source,
            event_type=event_type,
            content_type=ctype,
            object_id=object_id,
            event_time=event_time,
            extra_tags=extra_tags,
            extra_metadata={"original_filename": file_path.rsplit("/", 1)[-1]},
            extension=extension,
        )

    def get_object_tags(self, key: str) -> dict[str, str]:
        """Return the tag set for an existing object."""
        try:
            response = self._client.get_object_tagging(
                Bucket=self.settings.bucket,
                Key=key,
            )
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"Failed to read tags for '{key}': {exc}") from exc

        return {tag["Key"]: tag["Value"] for tag in response.get("TagSet", [])}

    def object_exists(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in the configured bucket."""
        try:
            self._client.head_object(Bucket=self.settings.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise StorageError(f"head_object failed for '{key}': {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_tags(
        self,
        *,
        source: str,
        event_type: str,
        object_id: str,
        event_time: datetime,
        extra: Optional[Mapping[str, str]],
    ) -> dict[str, str]:
        """Assemble the canonical tag set (S3 allows max 10 tags)."""
        tags: MutableMapping[str, str] = {
            "source": _truncate_tag(source),
            "event_type": _truncate_tag(event_type),
            "object_id": _truncate_tag(object_id),
            "ingested_at": event_time.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "layer": "raw",
        }
        if extra:
            for key, value in extra.items():
                if len(tags) >= 10:
                    logger.warning(
                        "S3 tag limit (10) reached; dropping tag '%s'", key
                    )
                    break
                tags[key] = _truncate_tag(value)
        return dict(tags)

    @staticmethod
    def _build_metadata(
        *,
        source: str,
        event_type: str,
        object_id: str,
        event_time: datetime,
        extra: Optional[Mapping[str, str]],
    ) -> dict[str, str]:
        """Assemble user-defined object metadata (x-amz-meta-* headers)."""
        meta: dict[str, str] = {
            "source": source,
            "event-type": event_type,
            "object-id": object_id,
            "ingested-at": event_time.astimezone(timezone.utc).isoformat(),
        }
        if extra:
            # S3 metadata keys must be ASCII; normalize to kebab-case-ish
            for key, value in extra.items():
                meta[key.replace("_", "-").lower()] = str(value)
        return meta


def _encode_tagging(tags: Mapping[str, str]) -> str:
    """Encode a tag dict as the ``Key=Value&Key=Value`` query string S3 expects."""
    from urllib.parse import quote_plus

    return "&".join(
        f"{quote_plus(k)}={quote_plus(v)}" for k, v in tags.items()
    )


def _sanitize_path_segment(value: str) -> str:
    """Make a string safe for use as an S3 key path segment."""
    cleaned = "".join(
        ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "_"
        for ch in value.strip().lower()
    )
    return cleaned.replace(":", "_") or "unknown"


def _truncate_tag(value: str, max_len: int = 256) -> str:
    """S3 tag values are limited to 256 Unicode characters."""
    return value[:max_len]
