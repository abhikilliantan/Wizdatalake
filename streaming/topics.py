"""Ensure Redpanda topics exist (idempotent)."""

from __future__ import annotations

import logging
from typing import Optional

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException

from streaming.config import KafkaSettings
from streaming.exceptions import TopicError

logger = logging.getLogger(__name__)


def _admin_client(settings: KafkaSettings) -> AdminClient:
    return AdminClient({"bootstrap.servers": settings.bootstrap_servers})


def topic_exists(name: str, *, settings: Optional[KafkaSettings] = None) -> bool:
    """Return True if ``name`` is already present on the cluster."""
    cfg = settings or KafkaSettings.from_env()
    admin = _admin_client(cfg)
    try:
        metadata = admin.list_topics(timeout=10)
    except KafkaException as exc:
        raise TopicError(f"Failed to list topics: {exc}") from exc
    return name in metadata.topics


def ensure_topic(
    name: Optional[str] = None,
    *,
    settings: Optional[KafkaSettings] = None,
    partitions: Optional[int] = None,
    replication_factor: Optional[int] = None,
) -> str:
    """Create ``datalake.ingest`` (or ``name``) if missing. Idempotent.

    ACL / SASL auth is deferred (local compose has no auth).
    """
    cfg = settings or KafkaSettings.from_env()
    topic = name or cfg.topic_ingest
    n_parts = partitions if partitions is not None else cfg.topic_partitions
    rf = (
        replication_factor
        if replication_factor is not None
        else cfg.topic_replication_factor
    )

    if topic_exists(topic, settings=cfg):
        logger.info("Topic already exists: %s", topic)
        return topic

    admin = _admin_client(cfg)
    new_topic = NewTopic(topic, num_partitions=n_parts, replication_factor=rf)
    futures = admin.create_topics([new_topic], request_timeout=15)

    future = futures[topic]
    try:
        future.result()
    except KafkaException as exc:
        # Race: another process created it between list and create.
        err = str(exc)
        if "TOPIC_ALREADY_EXISTS" in err or "already exists" in err.lower():
            logger.info("Topic already exists (race): %s", topic)
            return topic
        raise TopicError(f"Failed to create topic {topic!r}: {exc}") from exc

    logger.info(
        "Created topic %s partitions=%s replication_factor=%s",
        topic,
        n_parts,
        rf,
    )
    return topic
