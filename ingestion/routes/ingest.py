"""Webhook ingest routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from connectors.hub import IntegrationHub
from ingestion.auth import require_webhook_secret
from ingestion.deps import get_hub
from ingestion.schemas import IngestResponse
from storage import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/ingest",
    tags=["ingest"],
    dependencies=[Depends(require_webhook_secret)],
)


@router.post("/{source}", response_model=IngestResponse)
async def ingest_source(
    source: str,
    request: Request,
    hub: IntegrationHub = Depends(get_hub),
) -> IngestResponse:
    """Accept a JSON webhook for a registered ``source`` and land it in the lake."""
    source_key = source.strip().lower()
    if source_key not in hub.registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Unknown source '{source}'. "
                f"Registered: {', '.join(hub.registry.names())}"
            ),
        )

    try:
        body: Any = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request body must be valid JSON: {exc}",
        ) from exc

    if not isinstance(body, (dict, list)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON body must be an object or array",
        )

    try:
        result = hub.ingest_raw(source_key, body)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except StorageError as exc:
        logger.exception("Ingest storage failure source=%s", source_key)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to store event: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected ingest failure source=%s", source_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingest failed: {exc}",
        ) from exc

    return IngestResponse(
        status=result.status,
        source=result.source,
        event_type=result.event_type,
        object_id=result.object_id,
        object_key=result.object_key,
        catalog_id=result.catalog_id,
        byte_size=result.byte_size,
    )
