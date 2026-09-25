"""Health and observability routes."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from catalog.client import CatalogClient
from connectors.hub import IntegrationHub
from ingestion.deps import get_catalog, get_hub
from ingestion.schemas import CatalogListResponse, HealthResponse
from storage import StorageError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    hub: IntegrationHub = Depends(get_hub),
    catalog: CatalogClient = Depends(get_catalog),
) -> HealthResponse:
    minio_ok = False
    try:
        # Lightweight probe: ensure bucket is reachable
        hub.storage._client.head_bucket(Bucket=hub.storage.settings.bucket)
        minio_ok = True
    except (StorageError, Exception):  # noqa: BLE001
        minio_ok = False

    catalog_ok = catalog.ping()
    overall = "ok" if minio_ok and catalog_ok else "degraded"

    return HealthResponse(
        status=overall,
        app=os.environ.get("APP_NAME", "DataLakeSkM"),
        minio_ok=minio_ok,
        catalog_ok=catalog_ok,
        sources=hub.registry.names(),
    )


@router.get("/v1/catalog/recent", response_model=CatalogListResponse)
def recent_events(
    limit: int = 20,
    catalog: CatalogClient = Depends(get_catalog),
) -> CatalogListResponse:
    limit = max(1, min(limit, 100))
    rows = catalog.recent(limit=limit)
    return CatalogListResponse(count=len(rows), events=rows)
