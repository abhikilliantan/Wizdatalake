"""FastAPI webhook receiver for sales-app and custom application events."""

from ingestion.app import app, create_app

__all__ = ["app", "create_app"]
