"""API response models."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    minio_ok: bool
    catalog_ok: bool
    sources: list[str]


class IngestResponse(BaseModel):
    status: str
    source: str
    event_type: str
    object_id: str
    object_key: str
    catalog_id: Optional[int] = None
    byte_size: int
    message: str = "Event stored in raw data lake"


class ErrorResponse(BaseModel):
    detail: str
    source: Optional[str] = None


class CatalogEvent(BaseModel):
    id: int
    object_key: str
    source: str
    event_type: str
    object_id: Optional[str] = None
    status: str
    byte_size: Optional[int] = None
    created_at: Any = None


class CatalogListResponse(BaseModel):
    count: int
    events: list[CatalogEvent] = Field(default_factory=list)


class ServeObjectResponse(BaseModel):
    """Payload served from MinIO for an agent or application."""

    catalog_id: Optional[int] = None
    object_key: str
    source: str
    event_type: str
    object_id: Optional[str] = None
    content_type: str
    byte_size: int
    payload: Any
    message: str = "Object served from raw data lake"


class PresignResponse(BaseModel):
    object_key: str
    expires_seconds: int
    url: str
    message: str = "Time-limited GET URL for external download"
