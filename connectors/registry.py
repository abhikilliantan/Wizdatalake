"""Source adapter protocol and registry."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol

from connectors.envelope import EventEnvelope


class SourceAdapter(Protocol):
    """Maps a native webhook/body into an :class:`EventEnvelope`."""

    source_name: str

    def adapt(self, body: Mapping[str, Any] | list[Any]) -> EventEnvelope:
        ...


AdapterFactory = Callable[[], SourceAdapter]


class SourceRegistry:
    """Registers named source adapters used by the integration hub."""

    def __init__(self) -> None:
        self._adapters: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        key = adapter.source_name.strip().lower()
        if not key:
            raise ValueError("adapter.source_name must be non-empty")
        self._adapters[key] = adapter

    def get(self, source: str) -> SourceAdapter:
        key = source.strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            known = ", ".join(sorted(self._adapters)) or "(none)"
            raise KeyError(
                f"Unknown source '{source}'. Registered: {known}"
            ) from exc

    def names(self) -> list[str]:
        return sorted(self._adapters.keys())

    def __contains__(self, source: str) -> bool:
        return source.strip().lower() in self._adapters
