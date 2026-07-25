from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class TaskResult:
    id: str
    name: str
    status: Any
    result: Any = None
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0

    def is_pending(self) -> bool:
        return self.status == "pending"

    def is_running(self) -> bool:
        return self.status == "running"

    def is_completed(self) -> bool:
        return self.status == "completed"

    def is_failed(self) -> bool:
        return self.status == "failed"

    def is_retry(self) -> bool:
        return self.status == "retry"

    def is_cancelled(self) -> bool:
        return self.status == "cancelled"

    def is_timeout(self) -> bool:
        return self.status == "timeout"

    def is_done(self) -> bool:
        return self.status in {"completed", "failed", "cancelled", "timeout"}

    def get_duration(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": str(self.status),
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "duration": self.get_duration(),
        }
