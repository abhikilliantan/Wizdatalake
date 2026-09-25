"""Unit tests for streaming config + producer encoding (no live broker)."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from streaming.config import KafkaSettings
from streaming.exceptions import ProducerError
from streaming.producer import IngestProducer


def test_kafka_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)
    monkeypatch.delenv("KAFKA_TOPIC_INGEST", raising=False)
    settings = KafkaSettings.from_env()
    assert settings.bootstrap_servers == "localhost:19092"
    assert settings.topic_ingest == "datalake.ingest"
    assert settings.group_id == "datalake-streaming-consumer"


def test_kafka_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")
    monkeypatch.setenv("KAFKA_TOPIC_INGEST", "custom.topic")
    monkeypatch.setenv("KAFKA_GROUP_ID", "g1")
    monkeypatch.setenv("KAFKA_BATCH_SIZE", "50")
    settings = KafkaSettings.from_env()
    assert settings.bootstrap_servers == "broker:9092"
    assert settings.topic_ingest == "custom.topic"
    assert settings.group_id == "g1"
    assert settings.batch_size == 50


def test_producer_encode_and_produce_json() -> None:
    fake = MagicMock()
    settings = KafkaSettings(
        bootstrap_servers="localhost:19092",
        topic_ingest="datalake.ingest",
    )
    producer = IngestProducer(
        settings=settings,
        producer=fake,
        ensure_topic_on_init=False,
    )

    key = producer.produce_json(
        {"hello": "world"},
        key="k1",
        source="streaming",
        event_type="streaming.smoke",
    )
    assert key == "k1"
    fake.produce.assert_called_once()
    kwargs = fake.produce.call_args.kwargs
    assert kwargs["topic"] == "datalake.ingest"
    assert kwargs["key"] == b"k1"
    assert json.loads(kwargs["value"].decode()) == {"hello": "world"}
    hdrs = {h[0]: h[1] for h in kwargs["headers"]}
    assert hdrs["source"] == b"streaming"
    assert hdrs["event_type"] == b"streaming.smoke"
    assert hdrs["content-type"] == b"application/json"
    fake.poll.assert_called_with(0)

    fake.flush.return_value = 0
    assert producer.flush() == 0


def test_producer_flush_raises_on_remaining() -> None:
    fake = MagicMock()
    fake.flush.return_value = 2
    settings = KafkaSettings(bootstrap_servers="localhost:19092")
    producer = IngestProducer(
        settings=settings,
        producer=fake,
        ensure_topic_on_init=False,
    )
    with pytest.raises(ProducerError, match="still in queue"):
        producer.flush(timeout=1.0)


def test_producer_encode_bytes_and_str() -> None:
    assert IngestProducer._encode(b"raw") == b"raw"
    assert IngestProducer._encode("text") == b"text"
    assert json.loads(IngestProducer._encode({"a": 1}).decode()) == {"a": 1}
