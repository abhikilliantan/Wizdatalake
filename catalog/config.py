"""Catalog package configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CatalogSettings:
    """PostgreSQL connection settings for the metadata catalog."""

    database_url: str
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> CatalogSettings:
        url = os.environ.get("DATABASE_URL")
        if not url:
            user = os.environ.get("POSTGRES_USER", "datalake")
            password = os.environ.get("POSTGRES_PASSWORD", "datalake")
            host = os.environ.get("POSTGRES_HOST", "localhost")
            port = os.environ.get("POSTGRES_PORT", "5433")
            db = os.environ.get("POSTGRES_DB", "datalake")
            url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return cls(
            database_url=url,
            connect_timeout=int(os.environ.get("POSTGRES_CONNECT_TIMEOUT", "10")),
        )
