import asyncio

import pytest

from flaxon.tasks import RetryPolicy, Task, TaskQueue, TaskRegistry, Worker
from flaxon.tasks.backends.memory import MemoryBackend
from flaxon.tasks.result import TaskResult


@pytest.fixture
def task_registry():
    registry = TaskRegistry()

    def add_task(a: int, b: int) -> int:
        return a + b

    def multiply_task(a: int, b: int) -> int:
        return a * b

    async def async_task(name: str) -> str:
        await asyncio.sleep(0.1)
        return f"Hello, {name}!"

    registry.register("add", add_task)
    registry.register("multiply", multiply_task)
    registry.register("async_greeting", async_task)

    return registry


@pytest.fixture
def task_queue():
    return TaskQueue()


@pytest.mark.asyncio
async def test_task_execution(task_registry, task_queue):
    worker = Worker(task_registry, task_queue, concurrency=2)

    task = Task("add", task_registry.get("add"), args=(1, 2))
    await task_queue.push(task)

    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.5)
    await worker.stop()
    await worker_task

    result = await task_queue.get(task.id)
    assert result is not None
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_multiple_tasks(task_registry, task_queue):
    worker = Worker(task_registry, task_queue, concurrency=2)

    tasks = []
    for i in range(5):
        task = Task("add", task_registry.get("add"), args=(i, i + 1))
        await task_queue.push(task)
        tasks.append(task)

    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(1)
    await worker.stop()
    await worker_task

    for task in tasks:
        result = await task_queue.get(task.id)
        assert result is not None


@pytest.mark.asyncio
async def test_task_with_retry():
    retry_count = 0

    async def failing_task():
        nonlocal retry_count
        retry_count += 1
        if retry_count < 3:
            raise ValueError("Temporary failure")
        return "Success!"

    registry = TaskRegistry()
    registry.register("failing", failing_task)

    queue = TaskQueue()
    worker = Worker(registry, queue, concurrency=1)

    task = Task("failing", registry.get("failing"), retry_policy=RetryPolicy(delay=0, random_jitter=0))
    await queue.push(task)

    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(1)
    await worker.stop()
    await worker_task

    result = await queue.get(task.id)
    assert result is not None
    assert retry_count == 3


@pytest.mark.asyncio
async def test_task_result(task_registry, task_queue):
    worker = Worker(task_registry, task_queue, concurrency=1)

    task = Task("add", task_registry.get("add"), args=(1, 2))
    await task_queue.push(task)

    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.5)
    await worker.stop()
    await worker_task

    result = await task_queue.get(task.id)
    assert result is not None
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_worker_graceful_shutdown(task_registry, task_queue):
    worker = Worker(task_registry, task_queue, concurrency=2)

    for i in range(10):
        task = Task("async_greeting", task_registry.get("async_greeting"))
        await task_queue.push(task)

    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.5)
    await worker.stop()
    await worker_task

    assert worker.is_running() is False
