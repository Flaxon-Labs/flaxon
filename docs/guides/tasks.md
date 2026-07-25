
---

## docs/guides/tasks.md

```markdown
# Tasks

## Overview

Flaxon provides a task queue system for background job processing with retries, scheduling, and result storage.

## Defining Tasks

```python
from flaxon.tasks import task

@task(name="send_email")
async def send_email(to: str, subject: str, body: str):
    # Send email
    return {"sent": True, "to": to}

@task(name="process_image")
def process_image(image_path: str):
    # CPU-intensive processing
    return {"processed": True}

    Running Tasks
python
from flaxon.tasks import TaskQueue, TaskRegistry

registry = TaskRegistry()
queue = TaskQueue()

# Register tasks
registry.register("send_email", send_email)
registry.register("process_image", process_image)

# Push task to queue
task = Task("send_email", send_email, args=["user@example.com", "Hello", "World"])
await queue.push(task)

# Or use the registry
task = registry.create_task("send_email", args=["user@example.com", "Hello", "World"])
await queue.push(task)
Starting Workers
bash
# Start a worker
flaxon worker app:app --concurrency 4

# With specific queue
flaxon worker app:app --queue email --concurrency 2
Scheduling Tasks
python
from flaxon.tasks import Scheduler

scheduler = Scheduler(queue)

# Schedule a one-time task
scheduler.schedule(
    task=Task("send_email", send_email, args=["user@example.com", "Hello"]),
    delay=60,  # 60 seconds from now
)

# Schedule recurring task
scheduler.schedule(
    task=Task("process_image", process_image),
    interval=300,  # Every 5 minutes
)

# Scheduled decorator
from flaxon.tasks import scheduled_task

@scheduled_task(interval=60)
async def cleanup_tokens():
    # Run every minute
    await db.execute("DELETE FROM expired_tokens")
Task Results
python
task = Task("send_email", send_email, args=["user@example.com", "Hello"])
await queue.push(task)

# Poll for result
while True:
    result = await queue.get_result(task.id)
    if result.is_done():
        break
    await asyncio.sleep(1)

print(result.result)  # {"sent": True, "to": "user@example.com"}
Retry Policies
python
from flaxon.tasks import RetryPolicy

retry_policy = RetryPolicy(
    max_retries=5,
    delay=1.0,
    backoff=2.0,
    max_delay=60.0,
    random_jitter=0.1,
)

@task(
    name="retry_task",
    retry_policy=retry_policy,
)
async def retry_task():
    # Will retry up to 5 times with exponential backoff
    return {"success": True}
Task Timeouts
python
@task(name="timeout_task", timeout=30)
async def long_running_task():
    # Will be cancelled after 30 seconds
    return {"done": True}
Task Priorities
python
@task(name="high_priority", priority=10)
async def high_priority_task():
    pass

@task(name="low_priority", priority=0)
async def low_priority_task():
    pass
Task Signals
python
from flaxon.tasks import Signal, connect_signal

def on_success(task_id, result):
    print(f"Task {task_id} completed: {result}")

def on_failure(task_id, error):
    print(f"Task {task_id} failed: {error}")

connect_signal("my_task", Signal.ON_SUCCESS, on_success)
connect_signal("my_task", Signal.ON_FAILURE, on_failure)
Custom Backend
python
from flaxon.tasks.backends import CustomBackend

class RedisBackend:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def store_task(self, task):
        await self.redis.set(f"task:{task.id}", json.dumps(task.to_dict()))

    async def get_task(self, task_id):
        data = await self.redis.get(f"task:{task_id}")
        return Task.from_dict(json.loads(data))

backend = CustomBackend(RedisBackend(redis_client))
queue = TaskQueue(backend=backend)
Complete Example
python
from flaxon import Flaxon
from flaxon.tasks import (
    Task,
    TaskQueue,
    TaskRegistry,
    Worker,
    Scheduler,
    RetryPolicy,
    task,
)

app = Flaxon("tasks-demo")

# Define tasks
@task(name="send_email", retry_policy=RetryPolicy(max_retries=3))
async def send_email(to: str, subject: str, body: str):
    # Simulate sending email
    await asyncio.sleep(1)
    return {"sent": True, "to": to}

@task(name="process_report")
async def process_report(data: dict):
    return {"processed": True, "result": data}

# Setup
registry = TaskRegistry()
queue = TaskQueue()

registry.register("send_email", send_email)
registry.register("process_report", process_report)

@app.post("/send-email")
async def send_email_endpoint(request):
    data = await request.json()
    task = Task("send_email", send_email, args=[data["to"], data["subject"], data["body"]])
    await queue.push(task)
    return {"task_id": task.id, "status": "queued"}

@app.get("/task/<task_id>")
async def get_task_status(task_id: str):
    result = await queue.get_result(task_id)
    if result is None:
        return {"status": "not_found"}
    return result.to_dict()

# Worker endpoints
@app.post("/scheduler/start")
async def start_scheduler():
    scheduler = Scheduler(queue)
    await scheduler.start()
    return {"status": "started"}

# Health check
@app.get("/tasks/health")
async def tasks_health():
    return {
        "pending": await queue.pending_count(),
        "running": await queue.running_count(),
        "completed": await queue.completed_count(),
        "failed": await queue.failed_count(),
    }