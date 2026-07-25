from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    name: str
    data: Any = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            data=data.get("data"),
            created_at=created_at or datetime.now(),
            source=data.get("source"),
            metadata=data.get("metadata", {}),
        )


class DomainEvent(Event):
    def __init__(self, name: str, aggregate_id: str, data: Any = None, **kwargs: Any) -> None:
        super().__init__(name, data, **kwargs)
        self.aggregate_id = aggregate_id
        self.metadata["aggregate_id"] = aggregate_id

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["aggregate_id"] = self.aggregate_id
        return result


class IntegrationEvent(Event):
    def __init__(self, name: str, data: Any = None, **kwargs: Any) -> None:
        super().__init__(name, data, **kwargs)
        self.metadata["event_type"] = "integration"


class CommandEvent(Event):
    def __init__(self, name: str, data: Any = None, **kwargs: Any) -> None:
        super().__init__(name, data, **kwargs)
        self.metadata["event_type"] = "command"


class QueryEvent(Event):
    def __init__(self, name: str, data: Any = None, **kwargs: Any) -> None:
        super().__init__(name, data, **kwargs)
        self.metadata["event_type"] = "query"
