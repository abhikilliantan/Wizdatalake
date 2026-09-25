"""Environment-driven configuration for Redpanda / Kafka clients."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str | None = None) -> str:
    value = os.environ.get(key, default)
    if value is None or value == "":
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


@dataclass(frozen=True, slots=True)
class KafkaSettings:
    """Connection settings for the local Redpanda broker."""

    bootstrap_servers: str
    topic_ingest: str = "datalake.ingest"
    group_id: str = "datalake-streaming-consumer"
    batch_size: int = 100
    batch_timeout_ms: int = 5000
    auto_offset_reset: str = "earliest"
    topic_partitions: int = 1
    topic_replication_factor: int = 1

    @classmethod
    def from_env(cls) -> KafkaSettings:
        """Load settings from process environment (see ``.env.example``)."""
        return cls(
            bootstrap_servers=_env("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
            topic_ingest=_env("KAFKA_TOPIC_INGEST", "datalake.ingest"),
            group_id=_env("KAFKA_GROUP_ID", "datalake-streaming-consumer"),
            batch_size=int(os.environ.get("KAFKA_BATCH_SIZE", "100")),
            batch_timeout_ms=int(os.environ.get("KAFKA_BATCH_TIMEOUT_MS", "5000")),
            auto_offset_reset=_env("KAFKA_AUTO_OFFSET_RESET", "earliest"),
            topic_partitions=int(os.environ.get("KAFKA_TOPIC_PARTITIONS", "1")),
            topic_replication_factor=int(
                os.environ.get("KAFKA_TOPIC_REPLICATION_FACTOR", "1")
            ),
        )
