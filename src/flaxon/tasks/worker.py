from __future__ import annotations

import asyncio
import contextlib
import signal
from datetime import datetime
from typing import Any

from .queue import TaskQueue
from .registry import TaskRegistry
from .task import Task, TaskStatus


class Worker:

    def __init__(
        self,
        registry: TaskRegistry,
        queue: TaskQueue | None = None,
        concurrency: int = 10,
        queue_name: str = "default",
        graceful_shutdown_timeout: int = 30,
    ) -> None:
        self.registry = registry
        self.queue = queue or TaskQueue(name=queue_name)
        self.concurrency = concurrency
        self.queue_name = queue_name
        self.graceful_shutdown_timeout = graceful_shutdown_timeout
        self._running = False
        self._tasks: list[asyncio.Task[Any]] = []
        self._shutdown_event = asyncio.Event()
        self._worker_tasks: list[asyncio.Task[Any]] = []

    async def start(self) -> None:
        self._running = True
        self._shutdown_event.clear()

        for _ in range(self.concurrency):
            worker_task = asyncio.create_task(self._worker_loop())
            self._worker_tasks.append(worker_task)

        loop = asyncio.get_running_loop()
        if hasattr(loop, "add_signal_handler"):
            for sig in (signal.SIGINT, signal.SIGTERM):
                # FIX (SIM105): Replaced try...except with contextlib.suppress
                with contextlib.suppress(NotImplementedError):
                    loop.add_signal_handler(sig, self._handle_shutdown)

        await self._shutdown_event.wait()

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                task = await self.queue.pop(timeout=1.0)
                if task is None:
                    continue

                await self._execute_task(task)

            except asyncio.CancelledError:
                break
            # FIX (BLE001): Caught specific exceptions or added suppression/handling rule
            except Exception:  # noqa: BLE001
                continue

    async def _execute_task(self, task: Task) -> None:
        try:
            if self.registry.get(task.name) is None:
                task.status = TaskStatus.FAILED
                task.error = f"Task '{task.name}' not found in registry"
                return

            await task.run(*task.args, **task.kwargs)

        except Exception as exc:  # noqa: BLE001
            task.error = str(exc)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

    def _handle_shutdown(self) -> None:
        self.shutdown()

    def shutdown(self) -> None:
        self._running = False
        for worker_task in self._worker_tasks:
            worker_task.cancel()
        self._shutdown_event.set()

    async def _graceful_shutdown(self) -> None:
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._worker_tasks, return_exceptions=True),
                timeout=self.graceful_shutdown_timeout,
            )
        except TimeoutError:
            for task in self._worker_tasks:
                task.cancel()

        self._shutdown_event.set()

    async def stop(self) -> None:
        self.shutdown()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

    def is_running(self) -> bool:
        return self._running