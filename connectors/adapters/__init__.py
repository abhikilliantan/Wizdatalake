"""Built-in source adapters."""

from connectors.adapters.generic import GenericAdapter
from connectors.adapters.hubspot import HubSpotAdapter
from connectors.adapters.salesforce import SalesforceAdapter
from connectors.adapters.sap import SAPAdapter

__all__ = ["GenericAdapter", "HubSpotAdapter", "SalesforceAdapter", "SAPAdapter"]
