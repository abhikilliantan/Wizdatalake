"""Salesforce webhook → EventEnvelope adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from connectors.envelope import EventEnvelope


class SalesforceAdapter:
    """Maps Salesforce Change Event / Platform Event style payloads."""

    source_name = "salesforce"

    def adapt(self, body: Mapping[str, Any] | list[Any]) -> EventEnvelope:
        if isinstance(body, list):
            raise ValueError("Salesforce payload must be a JSON object")

        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else body
        header = (
            payload.get("ChangeEventHeader")
            if isinstance(payload.get("ChangeEventHeader"), dict)
            else {}
        )

        entity = str(header.get("entityName") or data.get("schema") or "Record")
        change_type = str(header.get("changeType") or "CHANGE").lower()
        event_type = f"{entity.lower()}.{change_type}"

        record_ids = header.get("recordIds") or []
        object_id = (
            str(record_ids[0])
            if isinstance(record_ids, list) and record_ids
            else str(payload.get("Id") or body.get("organizationId") or uuid4())
        )

        event_time = _parse_salesforce_time(body, header, payload)

        tags = {
            "crm": "salesforce",
            "entity": entity.lower(),
            "change_type": change_type,
        }
        org = body.get("organizationId")
        if org:
            tags["organization_id"] = str(org)[:256]

        return EventEnvelope(
            object_id=object_id,
            source=self.source_name,
            event_type=event_type,
            event_time=event_time,
            payload=dict(body),
            tags=tags,
        )


def _parse_salesforce_time(
    body: Mapping[str, Any],
    header: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> datetime:
    created = body.get("createdDate") or payload.get("LastModifiedDate")
    if isinstance(created, str):
        try:
            return datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            pass

    commit_ms = header.get("commitTimestamp")
    if isinstance(commit_ms, (int, float)):
        return datetime.fromtimestamp(commit_ms / 1000.0, tz=timezone.utc)

    return datetime.now(timezone.utc)
