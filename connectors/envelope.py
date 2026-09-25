"""Shared event envelope for all ingestion sources.

Every source adapter maps its native payload into this contract before
the hub writes to MinIO and the catalog.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EventEnvelope(BaseModel):
    """Normalized event passed through the integration hub."""

    object_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(..., min_length=1, description="Logical origin, e.g. salesforce")
    event_type: str = Field(..., min_length=1, description="e.g. contact.updated")
    event_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Mapping[str, Any] | list[Any]
    tags: dict[str, str] = Field(default_factory=dict)
    content_type: str = "application/json"

    @field_validator("source", "event_type")
    @classmethod
    def _strip_nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("event_time")
    @classmethod
    def _ensure_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def storage_tags(self) -> dict[str, str]:
        """Tags merged onto the MinIO object (extra + canonical)."""
        merged = {
            "source": self.source,
            "event_type": self.event_type,
            **self.tags,
        }
        return {k: str(v)[:256] for k, v in merged.items()}
