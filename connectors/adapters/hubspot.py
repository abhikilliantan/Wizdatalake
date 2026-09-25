"""HubSpot webhook → EventEnvelope adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from connectors.envelope import EventEnvelope


class HubSpotAdapter:
    """Maps HubSpot subscription / property-change webhook payloads."""

    source_name = "hubspot"

    def adapt(self, body: Mapping[str, Any] | list[Any]) -> EventEnvelope:
        # HubSpot often sends a list of events; take first or wrap.
        if isinstance(body, list):
            if not body:
                raise ValueError("HubSpot payload list is empty")
            if not isinstance(body[0], dict):
                raise ValueError("HubSpot events must be objects")
            event = body[0]
            raw_payload: Mapping[str, Any] | list[Any] = body
        else:
            event = dict(body)
            raw_payload = body

        subscription = str(
            event.get("subscriptionType") or event.get("eventType") or "contact.change"
        )
        object_id = str(
            event.get("objectId")
            or event.get("eventId")
            or uuid4()
        )

        occurred = event.get("occurredAt")
        if isinstance(occurred, (int, float)):
            # HubSpot uses epoch milliseconds
            event_time = datetime.fromtimestamp(occurred / 1000.0, tz=timezone.utc)
        else:
            event_time = datetime.now(timezone.utc)

        tags = {
            "crm": "hubspot",
            "subscription_type": subscription[:256],
        }
        portal = event.get("portalId")
        if portal is not None:
            tags["portal_id"] = str(portal)[:256]
        prop = event.get("propertyName")
        if prop:
            tags["property"] = str(prop)[:256]

        return EventEnvelope(
            object_id=object_id,
            source=self.source_name,
            event_type=subscription,
            event_time=event_time,
            payload=raw_payload if isinstance(raw_payload, dict) else {"events": raw_payload},
            tags=tags,
        )
