"""Integration hub: adapt → store → catalog."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from catalog.client import CatalogClient, CatalogWriteError
from connectors.adapters.generic import GenericAdapter
from connectors.adapters.hubspot import HubSpotAdapter
from connectors.adapters.salesforce import SalesforceAdapter
from connectors.adapters.sap import SAPAdapter
from connectors.envelope import EventEnvelope
from connectors.registry import SourceRegistry
from storage import ObjectStorage, StorageError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestResult:
    """Outcome of a single hub ingest."""

    object_key: str
    source: str
    event_type: str
    object_id: str
    catalog_id: Optional[int]
    status: str
    byte_size: int


class IntegrationHub:
    """Routes source payloads through adapters into MinIO + catalog."""

    def __init__(
        self,
        *,
        storage: Optional[ObjectStorage] = None,
        catalog: Optional[CatalogClient] = None,
        registry: Optional[SourceRegistry] = None,
    ) -> None:
        self.storage = storage or ObjectStorage()
        self.catalog = catalog or CatalogClient()
        self.registry = registry or build_default_registry()

    def ingest_raw(
        self,
        source: str,
        body: Mapping[str, Any] | list[Any],
    ) -> IngestResult:
        """Adapt a native body for ``source`` and persist it."""
        adapter = self.registry.get(source)
        envelope = adapter.adapt(body)
        return self.ingest_envelope(envelope)

    def ingest_envelope(self, envelope: EventEnvelope) -> IngestResult:
        """Persist an already-normalized envelope."""
        body_bytes = json.dumps(
            envelope.payload,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

        try:
            object_key = self.storage.put_json(
                envelope.payload if isinstance(envelope.payload, (dict, list)) else {"value": envelope.payload},
                source=envelope.source,
                event_type=envelope.event_type,
                object_id=envelope.object_id,
                event_time=envelope.event_time,
                extra_tags=envelope.tags,
            )
        except StorageError as exc:
            logger.exception(
                "Storage write failed source=%s event_type=%s",
                envelope.source,
                envelope.event_type,
            )
            self._record_failure(envelope, error=str(exc), byte_size=len(body_bytes))
            raise

        catalog_id: Optional[int] = None
        status = "stored"
        try:
            catalog_id = self.catalog.record_success(
                object_key=object_key,
                source=envelope.source,
                event_type=envelope.event_type,
                object_id=envelope.object_id,
                content_type=envelope.content_type,
                byte_size=len(body_bytes),
                tags=envelope.storage_tags(),
            )
        except CatalogWriteError as exc:
            # Object is in the lake; catalog failure must not hide that.
            status = "stored_catalog_pending"
            logger.error(
                "Catalog write failed after successful storage key=%s err=%s",
                object_key,
                exc,
            )

        logger.info(
            "Ingested source=%s event_type=%s key=%s catalog_id=%s status=%s",
            envelope.source,
            envelope.event_type,
            object_key,
            catalog_id,
            status,
        )
        return IngestResult(
            object_key=object_key,
            source=envelope.source,
            event_type=envelope.event_type,
            object_id=envelope.object_id,
            catalog_id=catalog_id,
            status=status,
            byte_size=len(body_bytes),
        )

    def _record_failure(
        self,
        envelope: EventEnvelope,
        *,
        error: str,
        byte_size: int,
    ) -> None:
        try:
            self.catalog.record_failure(
                object_key="",
                source=envelope.source,
                event_type=envelope.event_type,
                object_id=envelope.object_id,
                content_type=envelope.content_type,
                byte_size=byte_size,
                tags=envelope.storage_tags(),
                error_message=error,
            )
        except CatalogWriteError:
            logger.exception("Failed to record catalog failure row")


def build_default_registry() -> SourceRegistry:
    """Register Salesforce, HubSpot, SAP, and generic app adapters."""
    registry = SourceRegistry()
    registry.register(SalesforceAdapter())
    registry.register(HubSpotAdapter())
    registry.register(SAPAdapter())
    registry.register(GenericAdapter(source_name="app"))
    registry.register(GenericAdapter(source_name="custom"))
    return registry
