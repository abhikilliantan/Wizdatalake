"""Flat-file ingestion into the raw data lake.

Supports CSV and JSON files via multipart upload or the local drop folder
(``FILE_INGEST_DIR``, default ``./data/incoming``).
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from connectors.envelope import EventEnvelope
from connectors.hub import IngestResult, IntegrationHub

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".json", ".csv"}


class FileIngestError(ValueError):
    """Raised when a file cannot be parsed or ingested."""


def default_incoming_dir() -> Path:
    return Path(os.environ.get("FILE_INGEST_DIR", "./data/incoming")).expanduser()


def ingest_file_bytes(
    hub: IntegrationHub,
    *,
    filename: str,
    data: bytes,
    source: str = "file",
    extra_tags: Optional[dict[str, str]] = None,
) -> IngestResult:
    """Parse ``data`` as JSON or CSV and land it through the hub."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise FileIngestError(
            f"Unsupported file type '{suffix}'. Allowed: {sorted(SUPPORTED_SUFFIXES)}"
        )
    if not data:
        raise FileIngestError("File is empty")

    if suffix == ".json":
        payload = _parse_json(data)
        event_type = "file.json"
    else:
        payload = _parse_csv(data)
        event_type = "file.csv"

    tags = {
        "channel": "file",
        "original_filename": Path(filename).name[:256],
        **(extra_tags or {}),
    }
    envelope = EventEnvelope(
        object_id=str(uuid4()),
        source=source.strip().lower() or "file",
        event_type=event_type,
        event_time=datetime.now(timezone.utc),
        payload=payload,
        tags=tags,
    )
    return hub.ingest_envelope(envelope)


def ingest_path(hub: IntegrationHub, path: Path, *, source: str = "file") -> IngestResult:
    """Read a local path and ingest it."""
    if not path.is_file():
        raise FileIngestError(f"Not a file: {path}")
    return ingest_file_bytes(
        hub,
        filename=path.name,
        data=path.read_bytes(),
        source=source,
    )


def process_incoming_dir(
    hub: IntegrationHub,
    incoming: Optional[Path] = None,
    *,
    processed_dir: Optional[Path] = None,
    source: str = "file",
) -> list[IngestResult]:
    """Ingest every supported file in the drop folder, then move to processed/."""
    root = incoming or default_incoming_dir()
    root.mkdir(parents=True, exist_ok=True)
    dest = processed_dir or (root / "processed")
    dest.mkdir(parents=True, exist_ok=True)

    results: list[IngestResult] = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            logger.info("Skipping unsupported file %s", path.name)
            continue
        try:
            result = ingest_path(hub, path, source=source)
            results.append(result)
            target = dest / f"{path.stem}_{result.object_id[:8]}{path.suffix}"
            path.rename(target)
            logger.info("Ingested and archived %s → %s key=%s", path.name, target.name, result.object_key)
        except Exception:
            logger.exception("Failed to ingest drop file %s", path)
            raise
    return results


def _parse_json(data: bytes) -> dict[str, Any] | list[Any]:
    try:
        text = data.decode("utf-8-sig")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FileIngestError(f"Invalid JSON file: {exc}") from exc
    if not isinstance(parsed, (dict, list)):
        raise FileIngestError("JSON root must be an object or array")
    return parsed


def _parse_csv(data: bytes) -> dict[str, Any]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileIngestError(f"CSV must be UTF-8: {exc}") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise FileIngestError("CSV has no header row")
    rows = list(reader)
    return {
        "format": "csv",
        "columns": list(reader.fieldnames),
        "row_count": len(rows),
        "rows": rows,
    }
