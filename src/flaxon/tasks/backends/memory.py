from __future__ import annotations

import asyncio
from datetime import datetime

from ..exceptions import TaskNotFoundError
from ..result import TaskResult
from ..task import Task, TaskStatus


class MemoryBackend:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._results: dict[str, TaskResult] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def store_task(self, task: Task) -> None:
        async with self._lock:
            self._tasks[task.id] = task

    async def get_task(self, task_id: str) -> Task | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def get_task_required(self, task_id: str) -> Task:
        task = await self.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task '{task_id}' not found")
        return task

    async def remove_task(self, task_id: str) -> None:
        async with self._lock:
            self._tasks.pop(task_id, None)

    async def store_result(self, result: TaskResult) -> None:
        async with self._lock:
            self._results[result.id] = result

    async def get_result(self, task_id: str) -> TaskResult | None:
        async with self._lock:
            return self._results.get(task_id)

    async def get_result_required(self, task_id: str) -> TaskResult:
        result = await self.get_result(task_id)
        if result is None:
            raise TaskNotFoundError(f"Result for task '{task_id}' not found")
        return result

    async def remove_result(self, task_id: str) -> None:
        async with self._lock:
            self._results.pop(task_id, None)

    async def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        async with self._lock:
            if status is None:
                return list(self._tasks.values())
            return [t for t in self._tasks.values() if t.status == status]

    async def list_results(self, status: TaskStatus | None = None) -> list[TaskResult]:
        async with self._lock:
            if status is None:
                return list(self._results.values())
            return [r for r in self._results.values() if r.status == status]

    async def clear(self) -> None:
        async with self._lock:
            self._tasks.clear()
            self._results.clear()

    async def _cleanup_loop(self) -> None:
        while self._running:
            await asyncio.sleep(60)

            async with self._lock:
                now = datetime.now()
                to_remove = []

                for task_id, task in self._tasks.items():
                    if task.completed_at:
                        age = (now - task.completed_at).total_seconds()
                        if age > 3600:
                            to_remove.append(task_id)

                for task_id in to_remove:
                    self._tasks.pop(task_id, None)
                    self._results.pop(task_id, None)
