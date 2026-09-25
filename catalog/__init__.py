"""Catalog package — PostgreSQL metadata ledger."""

from catalog.client import CatalogClient
from catalog.config import CatalogSettings
from catalog.exceptions import CatalogError, CatalogWriteError

__all__ = [
    "CatalogClient",
    "CatalogSettings",
    "CatalogError",
    "CatalogWriteError",
]
