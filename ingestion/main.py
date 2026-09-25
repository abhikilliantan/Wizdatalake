"""ASGI entrypoint: ``python -m ingestion.main`` or uvicorn ingestion.app:app."""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    host = os.environ.get("INGESTION_HOST", "0.0.0.0")
    port = int(os.environ.get("INGESTION_PORT", "8000"))
    uvicorn.run(
        "ingestion.app:app",
        host=host,
        port=port,
        reload=os.environ.get("APP_ENV", "development") == "development",
        log_level=os.environ.get("LOG_LEVEL", "INFO").lower(),
    )


if __name__ == "__main__":
    main()
