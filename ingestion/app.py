"""FastAPI application for event-driven webhook ingestion."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routes import health, ingest
from storage.logging_config import configure_logging


def create_app() -> FastAPI:
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))

    app = FastAPI(
        title=os.environ.get("APP_NAME", "DataLakeSkM"),
        description=(
            "Event-driven webhook receiver for the DataLakeSkM foundation. "
            "Accepts Salesforce, HubSpot, and custom app events; stores raw "
            "payloads in MinIO and records them in the PostgreSQL catalog."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ingest.router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": "datalake-ingestion",
            "docs": "/docs",
            "health": "/health",
            "ingest": "/v1/ingest/{source}",
        }

    return app


app = create_app()
