from __future__ import annotations

from typing import Any

from ..exceptions import TaskNotFoundError
from ..result import TaskResult
from ..task import Task


class CustomBackend:
    def __init__(self, backend: Any) -> None:
        self.backend = backend

    async def start(self) -> None:
        if hasattr(self.backend, "start"):
            result = self.backend.start()
            if hasattr(result, "__await__"):
                await result

    async def stop(self) -> None:
        if hasattr(self.backend, "stop"):
            result = self.backend.stop()
            if hasattr(result, "__await__"):
                await result

    async def store_task(self, task: Task) -> None:
        if hasattr(self.backend, "store_task"):
            result = self.backend.store_task(task)
            if hasattr(result, "__await__"):
                await result
        elif hasattr(self.backend, "save_task"):
            result = self.backend.save_task(task)
            if hasattr(result, "__await__"):
                await result
        else:
            raise NotImplementedError("Backend does not support store_task")

    async def get_task(self, task_id: str) -> Task | None:
        if hasattr(self.backend, "get_task"):
            result = self.backend.get_task(task_id)
            if hasattr(result, "__await__"):
                return await result
            return result
        if hasattr(self.backend, "load_task"):
            result = self.backend.load_task(task_id)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Backend does not support get_task")

    async def get_task_required(self, task_id: str) -> Task:
        task = await self.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task '{task_id}' not found")
        return task

    async def remove_task(self, task_id: str) -> None:
        if hasattr(self.backend, "remove_task"):
            result = self.backend.remove_task(task_id)
            if hasattr(result, "__await__"):
                await result
        elif hasattr(self.backend, "delete_task"):
            result = self.backend.delete_task(task_id)
            if hasattr(result, "__await__"):
                await result
        else:
            raise NotImplementedError("Backend does not support remove_task")

    async def store_result(self, result: TaskResult) -> None:
        if hasattr(self.backend, "store_result"):
            result_obj = self.backend.store_result(result)
            if hasattr(result_obj, "__await__"):
                await result_obj
        elif hasattr(self.backend, "save_result"):
            result_obj = self.backend.save_result(result)
            if hasattr(result_obj, "__await__"):
                await result_obj
        else:
            raise NotImplementedError("Backend does not support store_result")

    async def get_result(self, task_id: str) -> TaskResult | None:
        if hasattr(self.backend, "get_result"):
            result = self.backend.get_result(task_id)
            if hasattr(result, "__await__"):
                return await result
            return result
        if hasattr(self.backend, "load_result"):
            result = self.backend.load_result(task_id)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Backend does not support get_result")

    async def get_result_required(self, task_id: str) -> TaskResult:
        result = await self.get_result(task_id)
        if result is None:
            raise TaskNotFoundError(f"Result for task '{task_id}' not found")
        return result

    async def remove_result(self, task_id: str) -> None:
        if hasattr(self.backend, "remove_result"):
            result = self.backend.remove_result(task_id)
            if hasattr(result, "__await__"):
                await result
        elif hasattr(self.backend, "delete_result"):
            result = self.backend.delete_result(task_id)
            if hasattr(result, "__await__"):
                await result
        else:
            raise NotImplementedError("Backend does not support remove_result")

    async def clear(self) -> None:
        if hasattr(self.backend, "clear"):
            result = self.backend.clear()
            if hasattr(result, "__await__"):
                await result
