from __future__ import annotations

import time
import uuid
from typing import Any


class Session:
    def __init__(
        self,
        session_id: str | None = None,
        data: dict[str, Any] | None = None,
        ttl: int = 86400,
        created_at: float | None = None,
    ) -> None:
        self.id = session_id or str(uuid.uuid4())
        self._data = data or {}
        self.ttl = ttl
        self.created_at = created_at or time.time()
        self._dirty = False

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._dirty = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._dirty = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def setdefault(self, key: str, default: Any) -> Any:
        if key not in self._data:
            self._data[key] = default
            self._dirty = True
        return self._data[key]

    def update(self, data: dict[str, Any]) -> None:
        self._data.update(data)
        self._dirty = True

    def clear(self) -> None:
        self._data.clear()
        self._dirty = True

    def pop(self, key: str, default: Any = None) -> Any:
        value = self._data.pop(key, default)
        self._dirty = True
        return value

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def values(self) -> list[Any]:
        return list(self._data.values())

    def items(self) -> list[tuple[str, Any]]:
        return list(self._data.items())

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl

    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False

    def touch(self) -> None:
        self.created_at = time.time()

    def regenerate(self) -> str:
        old_id = self.id
        self.id = str(uuid.uuid4())
        self._dirty = True
        return old_id

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "data": self._data,
            "ttl": self.ttl,
            "created_at": self.created_at,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Session:
        return cls(
            session_id=data.get("id"),
            data=data.get("data", {}),
            ttl=data.get("ttl", 86400),
            created_at=data.get("created_at"),
        )
