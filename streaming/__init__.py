"""Redpanda / Kafka streaming: topics, producer helper, smoke test.

Consumer batch-flush to MinIO lands in D12.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from streaming.exceptions import ProducerError, StreamingError, TopicError

if TYPE_CHECKING:
    from streaming.config import KafkaSettings
    from streaming.producer import IngestProducer

__all__ = [
    "KafkaSettings",
    "IngestProducer",
    "ensure_topic",
    "topic_exists",
    "StreamingError",
    "TopicError",
    "ProducerError",
]


def __getattr__(name: str):
    """Lazy-load confluent_kafka-backed modules."""
    if name == "KafkaSettings":
        from streaming.config import KafkaSettings

        return KafkaSettings
    if name == "IngestProducer":
        from streaming.producer import IngestProducer

        return IngestProducer
    if name == "ensure_topic":
        from streaming.topics import ensure_topic

        return ensure_topic
    if name == "topic_exists":
        from streaming.topics import topic_exists

        return topic_exists
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
