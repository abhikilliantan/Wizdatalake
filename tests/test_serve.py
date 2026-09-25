"""Tests for agent/application serving layer (/v1/serve)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from ingestion.app import create_app
from ingestion.deps import get_catalog, get_hub
from connectors.hub import IntegrationHub


class _MemStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_json(self, payload, **kwargs):  # noqa: ANN001
        key = (
            f"raw/source={kwargs['source']}/year=2026/month=09/day=25/"
            f"{kwargs['event_type']}_{kwargs['object_id']}.json"
        )
        body = json.dumps(payload, separators=(",", ":"), default=str).encode()
        self.objects[key] = body
        return key

    def get_bytes(self, key: str):
        if key not in self.objects:
            from storage import StorageError

            raise StorageError(f"Object not found: '{key}'")
        body = self.objects[key]
        return body, {"content_type": "application/json", "content_length": str(len(body))}

    def object_exists(self, key: str) -> bool:
        return key in self.objects

    def presign_get(self, key: str, *, expires_seconds: int = 3600) -> str:
        return f"http://minio.local/{key}?X-Amz-Expires={expires_seconds}"


class _MemCatalog:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self._id = 0

    def record_success(self, **kwargs):  # noqa: ANN001
        self._id += 1
        row = {
            "id": self._id,
            "object_key": kwargs["object_key"],
            "source": kwargs["source"],
            "event_type": kwargs["event_type"],
            "object_id": kwargs.get("object_id"),
            "content_type": kwargs.get("content_type") or "application/json",
            "status": "stored",
            "byte_size": kwargs.get("byte_size"),
            "tags": dict(kwargs.get("tags") or {}),
            "created_at": datetime.now(timezone.utc),
        }
        self.rows.append(row)
        return self._id

    def record_failure(self, **kwargs):  # noqa: ANN001
        return -1

    def search(self, **kwargs):  # noqa: ANN001
        source = kwargs.get("source")
        status = kwargs.get("status", "stored")
        limit = kwargs.get("limit", 20)
        out = []
        for r in reversed(self.rows):
            if status and r["status"] != status:
                continue
            if source and r["source"] != source:
                continue
            out.append(r)
            if len(out) >= limit:
                break
        return out

    def get_by_id(self, event_id: int):
        for r in self.rows:
            if r["id"] == event_id:
                return r
        return None

    def get_by_object_key(self, object_key: str):
        for r in reversed(self.rows):
            if r["object_key"] == object_key:
                return r
        return None

    def recent(self, *, limit: int = 20):
        return self.search(limit=limit, status=None)

    def ping(self) -> bool:
        return True


@pytest.fixture
def serve_client(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SHARED_SECRET", "test-secret")
    monkeypatch.setenv("AGENT_ACCESS_SECRET", "")
    storage = _MemStorage()
    catalog = _MemCatalog()
    hub = IntegrationHub(storage=storage, catalog=catalog)

    # Seed one event through the hub
    hub.ingest_raw(
        "app",
        {
            "event_type": "order.created",
            "object_id": "ord-serve-1",
            "payload": {"sku": "WIDGET", "qty": 2},
            "tags": {"demo": "serve"},
        },
    )

    app = create_app()
    app.dependency_overrides[get_hub] = lambda: hub
    app.dependency_overrides[get_catalog] = lambda: catalog
    client = TestClient(app)
    yield client, hub, catalog
    app.dependency_overrides.clear()


def test_serve_requires_auth(serve_client) -> None:
    client, _, _ = serve_client
    r = client.get("/v1/serve/events")
    assert r.status_code == 401


def test_serve_list_and_fetch_payload(serve_client) -> None:
    client, _, catalog = serve_client
    hdr = {"X-Agent-Key": "test-secret"}
    listed = client.get("/v1/serve/events", headers=hdr, params={"source": "app"})
    assert listed.status_code == 200
    body = listed.json()
    assert body["count"] >= 1
    event_id = body["events"][0]["id"]

    fetched = client.get(f"/v1/serve/events/{event_id}", headers=hdr)
    assert fetched.status_code == 200
    data = fetched.json()
    assert data["source"] == "app"
    assert data["payload"]["sku"] == "WIDGET"
    assert "object_key" in data


def test_serve_presign(serve_client) -> None:
    client, hub, _ = serve_client
    hdr = {"X-Webhook-Secret": "test-secret"}
    key = next(iter(hub.storage.objects))
    r = client.get(
        "/v1/serve/objects/presign",
        headers=hdr,
        params={"key": key, "expires_seconds": 120},
    )
    assert r.status_code == 200
    assert key in r.json()["url"]
    assert r.json()["expires_seconds"] == 120
