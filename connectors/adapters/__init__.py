"""Built-in source adapters."""

from connectors.adapters.generic import GenericAdapter
from connectors.adapters.hubspot import HubSpotAdapter
from connectors.adapters.salesforce import SalesforceAdapter

__all__ = ["GenericAdapter", "HubSpotAdapter", "SalesforceAdapter"]
