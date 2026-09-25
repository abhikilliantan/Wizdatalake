"""CLI: process files from the incoming drop folder.

Usage:
  PYTHONPATH=. python -m connectors.process_incoming
"""

from __future__ import annotations

from dotenv import load_dotenv

from connectors.file_ingest import default_incoming_dir, process_incoming_dir
from connectors.hub import IntegrationHub
from storage.logging_config import configure_logging


def main() -> None:
    load_dotenv()
    configure_logging()
    hub = IntegrationHub()
    incoming = default_incoming_dir()
    results = process_incoming_dir(hub, incoming)
    print(f"Processed {len(results)} file(s) from {incoming.resolve()}")
    for r in results:
        print(f"  {r.event_type} → {r.object_key} (catalog_id={r.catalog_id})")


if __name__ == "__main__":
    main()
