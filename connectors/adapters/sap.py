"""SAP S/4HANA / Event Mesh style webhook → EventEnvelope adapter.

Supports CloudEvents 1.0 envelopes commonly emitted by SAP Event Mesh
and Business Event Hub (e.g. BusinessPartner, SalesOrder changes).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from connectors.envelope import EventEnvelope


class SAPAdapter:
    """Maps SAP CloudEvents / business-event payloads into the hub envelope."""

    source_name = "sap"

    def adapt(self, body: Mapping[str, Any] | list[Any]) -> EventEnvelope:
        if isinstance(body, list):
            if not body:
                raise ValueError("SAP payload list is empty")
            if not isinstance(body[0], dict):
                raise ValueError("SAP events must be JSON objects")
            event = body[0]
            raw: Mapping[str, Any] | list[Any] = body
        else:
            event = dict(body)
            raw = body

        # CloudEvents fields
        ce_type = str(event.get("type") or event.get("eventType") or "")
        ce_id = str(event.get("id") or event.get("eventId") or uuid4())
        ce_source = str(event.get("source") or "")
        data = event.get("data") if isinstance(event.get("data"), dict) else event

        event_type = _derive_event_type(ce_type, data)
        object_id = _derive_object_id(data, ce_id)
        event_time = _parse_sap_time(event)

        tags: dict[str, str] = {
            "erp": "sap",
            "format": "cloudevents" if event.get("specversion") or ce_type else "business_event",
        }
        if ce_type:
            tags["sap_type"] = ce_type[:256]
        if ce_source:
            tags["sap_source"] = ce_source[:256]
        system_id = (
            event.get("systemId")
            or data.get("SystemID")
            or data.get("SenderBusinessSystemID")
        )
        if system_id:
            tags["system_id"] = str(system_id)[:256]
        plant = data.get("Plant") or data.get("plant") or data.get("Werks")
        if plant:
            tags["plant"] = str(plant)[:256]

        return EventEnvelope(
            object_id=object_id,
            source=self.source_name,
            event_type=event_type,
            event_time=event_time,
            payload=raw if isinstance(raw, dict) else {"events": raw},
            tags=tags,
        )


def _derive_event_type(ce_type: str, data: Mapping[str, Any]) -> str:
    if ce_type:
        # sap.s4.beh.businesspartner.v1.BusinessPartner.Changed.v1
        # → businesspartner.changed
        parts = [p for p in ce_type.split(".") if p]
        if len(parts) >= 2:
            entity = parts[-3] if len(parts) >= 3 else parts[-2]
            action = parts[-2] if parts[-1].startswith("v") else parts[-1]
            return f"{entity.lower()}.{action.lower()}"
        return ce_type.lower()

    entity = str(
        data.get("ObjectType")
        or data.get("BusinessObject")
        or data.get("Entity")
        or "businessobject"
    )
    action = str(data.get("Event") or data.get("ChangeType") or "changed")
    return f"{entity.lower()}.{action.lower()}"


def _derive_object_id(data: Mapping[str, Any], fallback: str) -> str:
    for key in (
        "BusinessPartner",
        "BusinessPartnerID",
        "SalesOrder",
        "SalesOrderID",
        "Material",
        "Product",
        "ObjectID",
        "Id",
        "ID",
        "key",
    ):
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return fallback


def _parse_sap_time(event: Mapping[str, Any]) -> datetime:
    time_val = event.get("time") or event.get("eventTime") or event.get("timestamp")
    if isinstance(time_val, str) and time_val.strip():
        try:
            return datetime.fromisoformat(time_val.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            pass
    if isinstance(time_val, (int, float)):
        ts = time_val / 1000.0 if time_val > 10_000_000_000 else float(time_val)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return datetime.now(timezone.utc)
