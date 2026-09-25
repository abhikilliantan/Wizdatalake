"""Generic / custom-application webhook adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from connectors.envelope import EventEnvelope


class GenericAdapter:
    """Accepts a flexible JSON body for custom applications.

    Expected (optional) fields:
    - ``event_type`` / ``type`` / ``eventType``
    - ``object_id`` / ``id``
    - ``event_time`` / ``timestamp`` (ISO-8601)
    - ``tags`` (object of string values)
    - ``payload`` (nested body; defaults to entire body)
    """

    def __init__(self, source_name: str = "app") -> None:
        self.source_name = source_name.strip().lower() or "app"

    def adapt(self, body: Mapping[str, Any] | list[Any]) -> EventEnvelope:
        if isinstance(body, list):
            payload: Mapping[str, Any] | list[Any] = {"items": body}
            meta: Mapping[str, Any] = {}
        else:
            meta = body
            nested = body.get("payload")
            payload = nested if isinstance(nested, (dict, list)) else body

        event_type = str(
            meta.get("event_type")
            or meta.get("eventType")
            or meta.get("type")
            or "event.received"
        )
        object_id = str(meta.get("object_id") or meta.get("id") or uuid4())
        event_time = _parse_time(meta.get("event_time") or meta.get("timestamp"))

        tags: dict[str, str] = {"channel": "webhook"}
        raw_tags = meta.get("tags")
        if isinstance(raw_tags, dict):
            for key, value in raw_tags.items():
                tags[str(key)[:64]] = str(value)[:256]

        return EventEnvelope(
            object_id=object_id,
            source=self.source_name,
            event_type=event_type,
            event_time=event_time,
            payload=payload if isinstance(payload, (dict, list)) else {"value": payload},
            tags=tags,
        )


def _parse_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            pass
    if isinstance(value, (int, float)):
        # treat large numbers as ms
        ts = value / 1000.0 if value > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return datetime.now(timezone.utc)
