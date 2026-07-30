from __future__ import annotations

from typing import Any


class ErrorStore:
    def __init__(self, max_errors: int = 1000) -> None:
        self._errors: dict[str, dict[str, Any]] = {}
        self._error_ids: list[str] = []
        self._max_errors = max_errors

    def store(self, error_data: dict[str, Any]) -> None:
        error_id = error_data.get("error_id")
        if not error_id:
            return

        self._errors[error_id] = error_data

        if error_id not in self._error_ids:
            self._error_ids.append(error_id)

        while len(self._error_ids) > self._max_errors:
            old_id = self._error_ids.pop(0)
            self._errors.pop(old_id, None)

    def get(self, error_id: str) -> dict[str, Any] | None:
        return self._errors.get(error_id)

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        ids = self._error_ids[-limit:]
        return [self._errors.get(eid, {}) for eid in ids]

    def get_by_type(self, error_type: str) -> list[dict[str, Any]]:
        return [e for e in self._errors.values() if e.get("type") == error_type]

    def get_by_path(self, path: str) -> list[dict[str, Any]]:
        return [e for e in self._errors.values() if e.get("path") == path]

    def count(self) -> int:
        return len(self._errors)

    def clear(self) -> None:
        self._errors.clear()
        self._error_ids.clear()

    def get_stats(self) -> dict[str, Any]:
        types = {}
        for error in self._errors.values():
            error_type = error.get("type", "Unknown")
            types[error_type] = types.get(error_type, 0) + 1

        return {
            "total": len(self._errors),
            "by_type": types,
            "newest": self._errors.get(self._error_ids[-1]) if self._error_ids else None,
            "oldest": self._errors.get(self._error_ids[0]) if self._error_ids else None,
        }
