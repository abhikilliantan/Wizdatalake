"""Redpanda / Kafka producer helper for the ingest topic."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional, Union
from uuid import uuid4

from confluent_kafka import KafkaException, Producer

from streaming.config import KafkaSettings
from streaming.exceptions import ProducerError
from streaming.topics import ensure_topic

logger = logging.getLogger(__name__)

JsonLike = Union[Mapping[str, Any], list[Any], str, bytes]


class IngestProducer:
    """Thin wrapper around ``confluent_kafka.Producer`` for ``datalake.ingest``.

    Ensures the target topic exists on first use. ACL/auth deferred.
    """

    def __init__(
        self,
        settings: Optional[KafkaSettings] = None,
        *,
        producer: Optional[Producer] = None,
        ensure_topic_on_init: bool = True,
    ) -> None:
        self.settings = settings or KafkaSettings.from_env()
        self._producer = producer or Producer(
            {
                "bootstrap.servers": self.settings.bootstrap_servers,
                "client.id": f"datalake-ingest-producer-{uuid4().hex[:8]}",
                "acks": "all",
                "enable.idempotence": True,
            }
        )
        self._topic = self.settings.topic_ingest
        if ensure_topic_on_init and producer is None:
            ensure_topic(self._topic, settings=self.settings)

    @property
    def topic(self) -> str:
        return self._topic

    def produce(
        self,
        value: JsonLike,
        *,
        key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        topic: Optional[str] = None,
    ) -> None:
        """Enqueue one message; call :meth:`flush` to wait for delivery."""
        target = topic or self._topic
        payload = self._encode(value)
        hdrs = (
            [(k, v.encode("utf-8")) for k, v in headers.items()] if headers else None
        )
        try:
            self._producer.produce(
                topic=target,
                key=key.encode("utf-8") if key is not None else None,
                value=payload,
                headers=hdrs,
                on_delivery=self._on_delivery,
            )
        except (BufferError, KafkaException) as exc:
            raise ProducerError(f"Produce failed for topic {target!r}: {exc}") from exc
        self._producer.poll(0)

    def produce_json(
        self,
        payload: Mapping[str, Any] | list[Any],
        *,
        key: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> str:
        """Produce a JSON object and return the message key used."""
        msg_key = key or str(uuid4())
        headers: dict[str, str] = {"content-type": "application/json"}
        if source:
            headers["source"] = source
        if event_type:
            headers["event_type"] = event_type
        self.produce(payload, key=msg_key, headers=headers)
        return msg_key

    def flush(self, timeout: float = 10.0) -> int:
        """Block until outstanding messages are delivered. Returns remaining count."""
        remaining = self._producer.flush(timeout)
        if remaining:
            raise ProducerError(
                f"{remaining} message(s) still in queue after flush timeout={timeout}s"
            )
        return remaining

    def close(self, timeout: float = 10.0) -> None:
        """Flush then release the underlying producer."""
        self.flush(timeout=timeout)

    @staticmethod
    def _encode(value: JsonLike) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        return json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")

    @staticmethod
    def _on_delivery(err: Optional[KafkaException], msg: Any) -> None:
        if err is not None:
            logger.error(
                "Delivery failed topic=%s partition=%s err=%s",
                msg.topic() if msg else "?",
                msg.partition() if msg else "?",
                err,
            )
            return
        logger.debug(
            "Delivered topic=%s partition=%s offset=%s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )
