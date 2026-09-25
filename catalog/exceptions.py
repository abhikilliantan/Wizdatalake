"""Catalog domain exceptions."""


class CatalogError(Exception):
    """Base catalog error."""


class CatalogWriteError(CatalogError):
    """Raised when inserting into ingestion_events fails."""
