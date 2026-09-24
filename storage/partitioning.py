"""Hive-style date partitioning helpers for the raw data-lake layer."""

from __future__ import annotations

from datetime import datetime, timezone


def build_partition_prefix(event_time: datetime, *, source: str) -> str:
    """Build an S3 key prefix of the form::

        raw/source=<source>/year=YYYY/month=MM/day=DD

    ``event_time`` is normalized to UTC before partitioning so that objects
    land in a consistent calendar day regardless of producer timezone.
    """
    ts = event_time.astimezone(timezone.utc)
    return (
        f"raw/source={source}"
        f"/year={ts.year:04d}"
        f"/month={ts.month:02d}"
        f"/day={ts.day:02d}"
    )
