"""Serve raw lake objects to external agents and applications.

MVP Agent Data Access Layer: discover via catalog, fetch MinIO payloads,
optionally issue time-limited presigned URLs.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, status

from catalog.client import CatalogClient
from catalog.exceptions import CatalogWriteError
from ingestion.auth_agent import require_agent_access
from ingestion.deps import get_catalog, get_hub
from ingestion.schemas import (
    CatalogEvent,
    CatalogListResponse,
    PresignResponse,
    ServeObjectResponse,
)
from connectors.hub import IntegrationHub
from storage import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/serve",
    tags=["serve"],
    dependencies=[Depends(require_agent_access)],
)


def _row_to_event(row: dict[str, Any]) -> CatalogEvent:
    return CatalogEvent(
        id=int(row["id"]),
        object_key=row["object_key"],
        source=row["source"],
        event_type=row["event_type"],
        object_id=row.get("object_id"),
        status=row["status"],
        byte_size=row.get("byte_size"),
        created_at=row.get("created_at"),
    )


def _decode_payload(body: bytes, content_type: str) -> Any:
    ctype = (content_type or "").lower()
    if "json" in ctype or body[:1] in (b"{", b"["):
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return {"_base64_hint": "binary payload — use presign endpoint", "byte_size": len(body)}


@router.get("/events", response_model=CatalogListResponse)
def list_events(
    source: Optional[str] = Query(default=None, description="Filter by source tag"),
    event_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    catalog: CatalogClient = Depends(get_catalog),
) -> CatalogListResponse:
    """Discover lake objects an agent may fetch (catalog index)."""
    try:
        rows = catalog.search(source=source, event_type=event_type, limit=limit)
    except CatalogWriteError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    events = [_row_to_event(r) for r in rows]
    return CatalogListResponse(count=len(events), events=events)


@router.get("/events/{event_id}", response_model=ServeObjectResponse)
def get_event_payload(
    event_id: int,
    catalog: CatalogClient = Depends(get_catalog),
    hub: IntegrationHub = Depends(get_hub),
) -> ServeObjectResponse:
    """Resolve a catalog id → MinIO object body (JSON when possible)."""
    try:
        row = catalog.get_by_id(event_id)
    except CatalogWriteError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail=f"Catalog event {event_id} not found")
    if row.get("status") != "stored":
        raise HTTPException(
            status_code=409,
            detail=f"Event {event_id} status is '{row.get('status')}', not stored",
        )
    key = row["object_key"]
    try:
        body, meta = hub.storage.get_bytes(key)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    content_type = row.get("content_type") or meta.get("content_type") or "application/json"
    return ServeObjectResponse(
        catalog_id=int(row["id"]),
        object_key=key,
        source=row["source"],
        event_type=row["event_type"],
        object_id=row.get("object_id"),
        content_type=content_type,
        byte_size=len(body),
        payload=_decode_payload(body, content_type),
    )


@router.get("/objects", response_model=ServeObjectResponse)
def get_object_by_key(
    key: str = Query(..., description="Full MinIO object key"),
    hub: IntegrationHub = Depends(get_hub),
    catalog: CatalogClient = Depends(get_catalog),
) -> ServeObjectResponse:
    """Fetch a raw object by lake key (for agents that already know the key)."""
    object_key = unquote(key).lstrip("/")
    try:
        body, meta = hub.storage.get_bytes(object_key)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    catalog_id = None
    source = "unknown"
    event_type = "unknown"
    object_id = None
    try:
        row = catalog.get_by_object_key(object_key)
        if row:
            catalog_id = int(row["id"])
            source = row["source"]
            event_type = row["event_type"]
            object_id = row.get("object_id")
    except CatalogWriteError:
        logger.warning("Catalog enrichment skipped for key=%s", object_key)

    content_type = meta.get("content_type") or "application/octet-stream"
    return ServeObjectResponse(
        catalog_id=catalog_id,
        object_key=object_key,
        source=source,
        event_type=event_type,
        object_id=object_id,
        content_type=content_type,
        byte_size=len(body),
        payload=_decode_payload(body, content_type),
    )


@router.get("/objects/presign", response_model=PresignResponse)
def presign_object(
    key: str = Query(..., description="Full MinIO object key"),
    expires_seconds: int = Query(default=3600, ge=60, le=86400),
    hub: IntegrationHub = Depends(get_hub),
) -> PresignResponse:
    """Issue a time-limited GET URL for an external application download."""
    object_key = unquote(key).lstrip("/")
    if not hub.storage.object_exists(object_key):
        raise HTTPException(status_code=404, detail=f"Object not found: {object_key}")
    try:
        url = hub.storage.presign_get(object_key, expires_seconds=expires_seconds)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return PresignResponse(
        object_key=object_key,
        expires_seconds=expires_seconds,
        url=url,
    )
