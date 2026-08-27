"""Case-insensitive HTTP header mapping."""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping


class Headers(MutableMapping[str, str]):
    """A case-insensitive mapping for HTTP headers."""

    def __init__(self, headers: dict[str, str] | list[tuple[bytes, bytes]] | None = None) -> None:
        self._items: dict[str, tuple[str, str]] = {}
        self._extra: list[tuple[str, str]] = []
        if headers:
            iterable = headers.items() if isinstance(headers, dict) else headers
            for key, value in iterable:
                name = key.decode("latin-1") if isinstance(key, bytes) else key
                text = value.decode("latin-1") if isinstance(value, bytes) else value
                self[name] = text

    def __getitem__(self, key: str) -> str:
        return self._items[key.lower()][1]

    def __setitem__(self, key: str, value: str) -> None:
        self._items[key.lower()] = (key.lower(), str(value))

    def __delitem__(self, key: str) -> None:
        del self._items[key.lower()]

    def add(self, key: str, value: str) -> None:
        """Append a header value, preserving repeated headers such as Set-Cookie."""
        self._extra.append((key.lower(), str(value)))

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def to_asgi(self) -> list[tuple[bytes, bytes]]:
        """Return headers encoded for an ASGI response."""
        headers = [(key.encode("latin-1"), value.encode("latin-1")) for key, value in self._items.values()]
        headers.extend((key.encode("latin-1"), value.encode("latin-1")) for key, value in self._extra)
        return headers
