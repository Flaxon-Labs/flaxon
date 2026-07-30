"""HTTP cookie helpers."""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from datetime import datetime


class Cookie:
    """A serializable HTTP cookie."""

    def __init__(self, key: str, value: str, **options: object) -> None:
        self.key = key
        self.value = value
        self.options = options

    def to_header(self) -> str:
        """Serialize the cookie to a ``Set-Cookie`` header value."""
        parts = [f"{self.key}={self.value}"]
        for key, value in self.options.items():
            if value is None or value is False:
                continue
            name = key.replace("_", "-").title()
            if value is True:
                parts.append(name)
            elif isinstance(value, datetime):
                parts.append(f"{name}={value.strftime('%a, %d %b %Y %H:%M:%S GMT')}")
            else:
                parts.append(f"{name}={value}")
        return "; ".join(parts)


class Cookies(MutableMapping[str, str]):
    """Dictionary-like request cookies with response cookie metadata."""

    def __init__(self, data: dict[str, str] | None = None) -> None:
        self._data = dict(data or {})
        self._cookies: dict[str, Cookie] = {}

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._cookies.pop(key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def set(self, key: str, value: str, **options: object) -> None:
        """Set a cookie and retain its response options."""
        self._data[key] = value
        self._cookies[key] = Cookie(key, value, **options)

    def delete(self, key: str) -> None:
        """Mark a cookie for deletion."""
        self.set(key, "", max_age=0, expires=datetime(1970, 1, 1))

    def to_headers(self) -> list[str]:
        """Return all pending ``Set-Cookie`` header values."""
        return [cookie.to_header() for cookie in self._cookies.values()]
