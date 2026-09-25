"""Tests for flat-file ingestion (AC-4)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from connectors.file_ingest import FileIngestError, ingest_file_bytes, process_incoming_dir
from storage.partitioning import build_partition_prefix


class _FakeStorage:
    def __init__(self) -> None:
        self.keys: list[str] = []
        self.payloads: list[object] = []

    def put_json(self, payload, **kwargs):  # noqa: ANN001
        from datetime import datetime, timezone

        ts = kwargs.get("event_time") or datetime.now(timezone.utc)
        prefix = build_partition_prefix(ts, source=kwargs["source"])
        key = f"{prefix}/{kwargs['event_type']}_{kwargs['object_id']}.json"
        self.keys.append(key)
        self.payloads.append(payload)
        return key


class _FakeCatalog:
    def __init__(self) -> None:
        self.ids = 0

    def record_success(self, **kwargs):  # noqa: ANN001
        self.ids += 1
        return self.ids

    def record_failure(self, **kwargs):  # noqa: ANN001
        return -1


_PARTITION_RE = re.compile(
    r"^raw/source=[^/]+/year=\d{4}/month=\d{2}/day=\d{2}/.+\.json$"
)


@pytest.fixture
def hub():
    from connectors.hub import IntegrationHub

    storage = _FakeStorage()
    catalog = _FakeCatalog()
    return IntegrationHub(storage=storage, catalog=catalog), storage, catalog


def test_ingest_json_bytes(hub) -> None:
    h, storage, catalog = hub
    result = ingest_file_bytes(
        h,
        filename="orders.json",
        data=json.dumps([{"id": 1}, {"id": 2}]).encode(),
        source="file",
    )
    assert result.event_type == "file.json"
    assert result.status == "stored"
    assert result.catalog_id == 1
    assert "source=file" in result.object_key
    assert _PARTITION_RE.match(result.object_key), result.object_key
    assert storage.keys


def test_ingest_csv_bytes_partition_path(hub) -> None:
    """AC-4: CSV lands under raw/source=…/year=…/month=…/day=…"""
    h, storage, _ = hub
    csv_data = Path("tests/fixtures/sample_stock.csv").read_bytes()
    result = ingest_file_bytes(h, filename="sample_stock.csv", data=csv_data, source="file")
    assert result.event_type == "file.csv"
    assert result.status == "stored"
    assert _PARTITION_RE.match(result.object_key), result.object_key
    assert "source=file" in result.object_key
    assert storage.payloads[0]["row_count"] == 3
    assert storage.payloads[0]["columns"] == ["sku", "qty", "plant"]


def test_reject_unsupported(hub) -> None:
    h, _, _ = hub
    with pytest.raises(FileIngestError):
        ingest_file_bytes(h, filename="notes.txt", data=b"hello", source="file")


def test_process_incoming_dir(hub, tmp_path: Path) -> None:
    h, _, _ = hub
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "batch.json").write_text('{"ok": true}', encoding="utf-8")
    results = process_incoming_dir(h, incoming, source="file")
    assert len(results) == 1
    assert not (incoming / "batch.json").exists()
    assert list((incoming / "processed").glob("batch_*.json"))
    assert _PARTITION_RE.match(results[0].object_key)


def test_upload_api_csv(hub, monkeypatch: pytest.MonkeyPatch) -> None:
    h, _, _ = hub
    monkeypatch.setenv("WEBHOOK_SHARED_SECRET", "test-secret")

    from ingestion.app import create_app
    from ingestion.deps import get_hub

    app = create_app()
    app.dependency_overrides[get_hub] = lambda: h
    client = TestClient(app)
    csv_data = b"sku,qty\nWIDGET,3\n"
    response = client.post(
        "/v1/files/upload",
        headers={"X-Webhook-Secret": "test-secret"},
        files={"file": ("stock.csv", csv_data, "text/csv")},
        data={"source": "file"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["event_type"] == "file.csv"
    assert body["status"] == "stored"
    assert _PARTITION_RE.match(body["object_key"]), body["object_key"]
