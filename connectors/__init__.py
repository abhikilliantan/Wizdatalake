"""Connectors package — source adapters and integration hub."""

from connectors.envelope import EventEnvelope
from connectors.hub import IngestResult, IntegrationHub, build_default_registry
from connectors.registry import SourceRegistry

__all__ = [
    "EventEnvelope",
    "IngestResult",
    "IntegrationHub",
    "SourceRegistry",
    "build_default_registry",
]
