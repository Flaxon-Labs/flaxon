from __future__ import annotations

import time
from typing import Any


class QuerySnapshot:
    def __init__(self, query: str, params: tuple | None = None, duration: float = 0) -> None:
        self.query = query
        self.params = params or ()
        self.duration = duration
        self.timestamp = time.time()
        self._result_preview = None

    def set_result_preview(self, result: Any, limit: int = 5) -> None:
        if isinstance(result, list):
            self._result_preview = result[:limit]
        elif isinstance(result, dict):
            self._result_preview = {k: v for k, v in list(result.items())[:limit]}
        else:
            self._result_preview = result

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "query": self.query,
            "params": self.params,
            "duration_ms": round(self.duration * 1000, 2),
            "result_preview": self._result_preview,
        }

    @classmethod
    def from_execution(cls, query: str, params: tuple | None = None, duration: float = 0) -> QuerySnapshot:
        return cls(query, params, duration)


class QuerySnapshotCollector:
    def __init__(self, max_snapshots: int = 50) -> None:
        self._snapshots: list[QuerySnapshot] = []
        self._max_snapshots = max_snapshots

    def add(self, snapshot: QuerySnapshot) -> None:
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

    def clear(self) -> None:
        self._snapshots.clear()

    def get_all(self) -> list[QuerySnapshot]:
        return self._snapshots.copy()

    def get_slow_queries(self, threshold: float = 0.1) -> list[QuerySnapshot]:
        return [s for s in self._snapshots if s.duration > threshold]

    def get_recent(self, count: int = 10) -> list[QuerySnapshot]:
        return self._snapshots[-count:]

    def to_dict(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._snapshots]

    def __len__(self) -> int:
        return len(self._snapshots)

    def __iter__(self):
        return iter(self._snapshots)
