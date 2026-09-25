"""Flat file upload + drop-folder processing routes."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from connectors.file_ingest import (
    FileIngestError,
    default_incoming_dir,
    ingest_file_bytes,
    process_incoming_dir,
)
from connectors.hub import IntegrationHub
from ingestion.auth import require_webhook_secret
from ingestion.deps import get_hub
from ingestion.schemas import IngestResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/files",
    tags=["files"],
    dependencies=[Depends(require_webhook_secret)],
)


@router.post("/upload", response_model=IngestResponse)
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form(default="file"),
    hub: IntegrationHub = Depends(get_hub),
) -> IngestResponse:
    """Upload a CSV or JSON file into the raw lake."""
    filename = file.filename or "upload.bin"
    data = await file.read()
    try:
        result = ingest_file_bytes(
            hub,
            filename=filename,
            data=data,
            source=source,
        )
    except FileIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("File upload failed name=%s", filename)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to store file: {exc}",
        ) from exc

    return IngestResponse(
        status=result.status,
        source=result.source,
        event_type=result.event_type,
        object_id=result.object_id,
        object_key=result.object_key,
        catalog_id=result.catalog_id,
        byte_size=result.byte_size,
        message=f"File '{filename}' stored in raw data lake",
    )


@router.post("/process-incoming")
def process_incoming(
    hub: IntegrationHub = Depends(get_hub),
    source: str = "file",
) -> dict:
    """Process all CSV/JSON files sitting in ``FILE_INGEST_DIR``."""
    incoming = default_incoming_dir()
    try:
        results = process_incoming_dir(hub, incoming, source=source)
    except FileIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Incoming folder processing failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "incoming_dir": str(incoming.resolve()),
        "processed": len(results),
        "results": [
            {
                "object_key": r.object_key,
                "catalog_id": r.catalog_id,
                "event_type": r.event_type,
                "status": r.status,
            }
            for r in results
        ],
    }
