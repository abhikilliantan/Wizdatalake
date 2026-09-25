"""Unit tests for source adapters."""

from __future__ import annotations

import json
from pathlib import Path

from connectors.adapters.generic import GenericAdapter
from connectors.adapters.hubspot import HubSpotAdapter
from connectors.adapters.salesforce import SalesforceAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_salesforce_adapter_fixture() -> None:
    body = json.loads((FIXTURES / "salesforce_contact_updated.json").read_text())
    envelope = SalesforceAdapter().adapt(body)
    assert envelope.source == "salesforce"
    assert envelope.event_type == "contact.update"
    assert envelope.object_id == "0035g00000XXXXX"
    assert envelope.tags["entity"] == "contact"


def test_hubspot_adapter_fixture() -> None:
    body = json.loads(
        (FIXTURES / "hubspot_contact_property_change.json").read_text()
    )
    envelope = HubSpotAdapter().adapt(body)
    assert envelope.source == "hubspot"
    assert envelope.event_type == "contact.propertyChange"
    assert envelope.object_id == "451"
    assert envelope.tags["property"] == "email"


def test_generic_adapter() -> None:
    envelope = GenericAdapter(source_name="app").adapt(
        {
            "event_type": "order.created",
            "object_id": "ord-1",
            "payload": {"total": 42},
            "tags": {"tenant": "acme"},
        }
    )
    assert envelope.source == "app"
    assert envelope.event_type == "order.created"
    assert envelope.object_id == "ord-1"
    assert envelope.payload == {"total": 42}
    assert envelope.tags["tenant"] == "acme"
