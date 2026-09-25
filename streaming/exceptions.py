"""Streaming / Redpanda error types."""


class StreamingError(Exception):
    """Base error for the streaming package."""


class TopicError(StreamingError):
    """Topic create / describe failures."""


class ProducerError(StreamingError):
    """Produce / delivery failures."""
