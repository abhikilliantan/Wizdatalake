"""Unit tests for Hive-style partition prefix generation."""

from __future__ import annotations

from datetime import datetime, timezone

from storage.partitioning import build_partition_prefix


def test_build_partition_prefix_utc() -> None:
    ts = datetime(2024, 9, 24, 14, 30, 0, tzinfo=timezone.utc)
    prefix = build_partition_prefix(ts, source="salesforce")
    assert prefix == "raw/source=salesforce/year=2024/month=09/day=24"


def test_build_partition_prefix_normalizes_to_utc() -> None:
    # 2024-09-24 22:00 EDT == 2024-09-25 02:00 UTC → day=25
    from datetime import timedelta

    edt = timezone(timedelta(hours=-4))
    ts = datetime(2024, 9, 24, 22, 0, 0, tzinfo=edt)
    prefix = build_partition_prefix(ts, source="hubspot")
    assert prefix == "raw/source=hubspot/year=2024/month=09/day=25"
