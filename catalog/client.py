"""PostgreSQL catalog client for ingestion_events."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional

import psycopg
from psycopg.rows import dict_row

from catalog.config import CatalogSettings
from catalog.exceptions import CatalogWriteError

logger = logging.getLogger(__name__)


class CatalogClient:
    """Writes and reads rows in ``ingestion_events``."""

    def __init__(self, settings: Optional[CatalogSettings] = None) -> None:
        self.settings = settings or CatalogSettings.from_env()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(
            self.settings.database_url,
            connect_timeout=self.settings.connect_timeout,
            row_factory=dict_row,
        )

    def record_success(
        self,
        *,
        object_key: str,
        source: str,
        event_type: str,
        object_id: Optional[str],
        content_type: Optional[str],
        byte_size: int,
        tags: Mapping[str, str],
    ) -> int:
        return self._insert(
            object_key=object_key,
            source=source,
            event_type=event_type,
            object_id=object_id,
            content_type=content_type,
            byte_size=byte_size,
            tags=tags,
            status="stored",
            error_message=None,
        )

    def record_failure(
        self,
        *,
        object_key: str,
        source: str,
        event_type: str,
        object_id: Optional[str],
        content_type: Optional[str],
        byte_size: int,
        tags: Mapping[str, str],
        error_message: str,
    ) -> int:
        return self._insert(
            object_key=object_key or f"failed/{source}/{object_id or 'unknown'}",
            source=source,
            event_type=event_type,
            object_id=object_id,
            content_type=content_type,
            byte_size=byte_size,
            tags=tags,
            status="failed",
            error_message=error_message[:2000],
        )

    def _insert(
        self,
        *,
        object_key: str,
        source: str,
        event_type: str,
        object_id: Optional[str],
        content_type: Optional[str],
        byte_size: int,
        tags: Mapping[str, str],
        status: str,
        error_message: Optional[str],
    ) -> int:
        sql = """
            INSERT INTO ingestion_events (
                object_key, source, event_type, object_id,
                content_type, byte_size, tags, status, error_message
            )
            VALUES (
                %(object_key)s, %(source)s, %(event_type)s, %(object_id)s,
                %(content_type)s, %(byte_size)s, %(tags)s::jsonb,
                %(status)s, %(error_message)s
            )
            RETURNING id
        """
        params: dict[str, Any] = {
            "object_key": object_key,
            "source": source,
            "event_type": event_type,
            "object_id": object_id,
            "content_type": content_type,
            "byte_size": byte_size,
            "tags": json.dumps(dict(tags)),
            "status": status,
            "error_message": error_message,
        }
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    row = cur.fetchone()
                conn.commit()
        except Exception as exc:  # noqa: BLE001 — wrap driver errors
            logger.exception("Catalog insert failed source=%s", source)
            raise CatalogWriteError(f"Failed to write ingestion_events: {exc}") from exc

        if not row or "id" not in row:
            raise CatalogWriteError("Catalog insert returned no id")
        return int(row["id"])

    def recent(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return the latest catalog rows (for health / demo)."""
        sql = """
            SELECT id, object_key, source, event_type, object_id,
                   status, byte_size, created_at
            FROM ingestion_events
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, {"limit": limit})
                    rows = cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            raise CatalogWriteError(f"Failed to query catalog: {exc}") from exc
        return [dict(r) for r in rows]

    def ping(self) -> bool:
        """Return True if the database accepts connections."""
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    row = cur.fetchone()
            return bool(row and row.get("ok") == 1)
        except Exception:  # noqa: BLE001
            logger.exception("Catalog ping failed")
            return False
