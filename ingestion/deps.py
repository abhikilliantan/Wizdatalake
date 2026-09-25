"""FastAPI dependency wiring for the ingestion service."""

from __future__ import annotations

from functools import lru_cache

from catalog.client import CatalogClient
from connectors.hub import IntegrationHub
from storage import ObjectStorage
from storage.logging_config import configure_logging


@lru_cache(maxsize=1)
def get_hub() -> IntegrationHub:
    """Process-wide hub singleton (storage + catalog + registry)."""
    configure_logging()
    return IntegrationHub(
        storage=ObjectStorage(),
        catalog=CatalogClient(),
    )


def get_catalog() -> CatalogClient:
    return get_hub().catalog
