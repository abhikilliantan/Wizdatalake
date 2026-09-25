"""Tests for flat-file ingestion (AC-4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from connectors.file_ingest import FileIngestError, ingest_file_bytes, process_incoming_dir


class _FakeStorage:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def put_json(self, payload, **kwargs):  # noqa: ANN001
        key = (
            f"raw/source={kwargs['source']}/year=2026/month=09/day=25/"
            f"{kwargs['event_type']}_{kwargs['object_id']}.json"
        )
        self.keys.append(key)
        return key


class _FakeCatalog:
    def __init__(self) -> None:
        self.ids = 0

    def record_success(self, **kwargs):  # noqa: ANN001
        self.ids += 1
        return self.ids

    def record_failure(self, **kwargs):  # noqa: ANN001
        return -1


@pytest.fixture
def hub(monkeypatch: pytest.MonkeyPatch):
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
    assert storage.keys


def test_ingest_csv_bytes(hub) -> None:
    h, _, _ = hub
    csv_data = b"sku,qty\nWIDGET,3\nGADGET,1\n"
    result = ingest_file_bytes(h, filename="stock.csv", data=csv_data, source="file")
    assert result.event_type == "file.csv"
    assert result.status == "stored"


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
