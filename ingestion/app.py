"""FastAPI application for event-driven webhook ingestion."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routes import files, health, ingest, serve
from storage.logging_config import configure_logging


def create_app() -> FastAPI:
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))

    app = FastAPI(
        title=os.environ.get("APP_NAME", "DataLakeSkM"),
        description=(
            "Event-driven webhook + file receiver and agent serving API for DataLakeSkM. "
            "Ingests Salesforce, HubSpot, SAP, custom app events, and CSV/JSON files into MinIO; "
            "serves discovery + payloads to external agents/apps via /v1/serve/*."
        ),
        version="0.3.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(files.router)
    app.include_router(serve.router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": "datalake-ingestion",
            "docs": "/docs",
            "health": "/health",
            "ingest": "/v1/ingest/{source}",
            "files": "/v1/files/upload",
            "serve_events": "/v1/serve/events",
            "serve_event": "/v1/serve/events/{id}",
            "serve_object": "/v1/serve/objects?key=",
            "serve_presign": "/v1/serve/objects/presign?key=",
        }

    return app


app = create_app()
