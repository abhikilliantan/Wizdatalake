"""Produce/consume smoke test against local Redpanda.

Usage::

    PYTHONPATH=. python -m streaming.smoke
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Consumer, KafkaException

from streaming.config import KafkaSettings
from streaming.producer import IngestProducer
from streaming.topics import ensure_topic, topic_exists

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("streaming.smoke")


def run_smoke(*, timeout_s: float = 30.0) -> dict:
    """Ensure topic, produce one message, consume it back. Returns result dict."""
    settings = KafkaSettings.from_env()
    topic = ensure_topic(settings=settings)
    assert topic_exists(topic, settings=settings), f"topic missing after ensure: {topic}"

    marker = f"smoke-{uuid4().hex}"
    payload = {
        "event_type": "streaming.smoke",
        "object_id": marker,
        "event_time": datetime.now(timezone.utc).isoformat(),
        "payload": {"hello": "redpanda", "marker": marker},
        "tags": {"smoke": "true"},
    }

    producer = IngestProducer(settings=settings, ensure_topic_on_init=False)
    key = producer.produce_json(
        payload,
        key=marker,
        source="streaming",
        event_type="streaming.smoke",
    )
    producer.flush()
    logger.info("Produced key=%s topic=%s", key, topic)

    group = f"datalake-smoke-{uuid4().hex[:10]}"
    consumer = Consumer(
        {
            "bootstrap.servers": settings.bootstrap_servers,
            "group.id": group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([topic])

    deadline = time.monotonic() + timeout_s
    found = None
    try:
        while time.monotonic() < deadline:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            value = msg.value()
            if value is None:
                continue
            body = json.loads(value.decode("utf-8"))
            if body.get("object_id") == marker or (
                isinstance(body.get("payload"), dict)
                and body["payload"].get("marker") == marker
            ):
                found = {
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "key": msg.key().decode("utf-8") if msg.key() else None,
                    "body": body,
                }
                consumer.commit(message=msg, asynchronous=False)
                break
    finally:
        consumer.close()

    if found is None:
        raise RuntimeError(
            f"Smoke consume timed out after {timeout_s}s looking for marker={marker}"
        )

    # Confirm topic is still listed (exit criterion: topic exists)
    assert topic_exists(topic, settings=settings)

    result = {
        "ok": True,
        "topic": topic,
        "produced_key": key,
        "consumed": found,
        "bootstrap": settings.bootstrap_servers,
    }
    logger.info(
        "Smoke OK topic=%s offset=%s partition=%s",
        found["topic"],
        found["offset"],
        found["partition"],
    )
    return result


def main() -> int:
    # Load .env when present (local demo convenience).
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    try:
        result = run_smoke()
    except Exception as exc:  # noqa: BLE001 — CLI surface
        logger.error("Smoke FAILED: %s", exc)
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
