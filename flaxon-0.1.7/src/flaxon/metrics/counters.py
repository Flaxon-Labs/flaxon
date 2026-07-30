from __future__ import annotations

import threading
from typing import Any


class Counter:
    def __init__(self, name: str, help_text: str = "", labels: list[str] | None = None) -> None:
        self.name = name
        self.help_text = help_text
        self.labels = labels or []
        self._values: dict[str, int] = {}
        self._lock = threading.Lock()

    def _key(self, **labels: Any) -> str:
        if not self.labels:
            return ""
        return ",".join(f"{k}={labels.get(k)}" for k in self.labels)

    def inc(self, value: int = 1, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: int = 1, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) - value

    def reset(self, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = 0

    def get(self, **labels: Any) -> int:
        key = self._key(**labels)
        return self._values.get(key, 0)

    def get_all(self) -> dict[str, int]:
        return dict(self._values)

    def get_metrics(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "help": self.help_text,
            "values": dict(self._values),
        }


class Gauge:
    def __init__(self, name: str, help_text: str = "", labels: list[str] | None = None) -> None:
        self.name = name
        self.help_text = help_text
        self.labels = labels or []
        self._values: dict[str, float] = {}
        self._lock = threading.Lock()

    def _key(self, **labels: Any) -> str:
        if not self.labels:
            return ""
        return ",".join(f"{k}={labels.get(k)}" for k in self.labels)

    def set(self, value: float, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = value

    def inc(self, value: float = 1.0, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def dec(self, value: float = 1.0, **labels: Any) -> None:
        key = self._key(**labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) - value

    def get(self, **labels: Any) -> float:
        key = self._key(**labels)
        return self._values.get(key, 0.0)

    def get_all(self) -> dict[str, float]:
        return dict(self._values)

    def get_metrics(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "help": self.help_text,
            "values": dict(self._values),
        }
