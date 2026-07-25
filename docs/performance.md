
---

## docs/performance.md

```markdown
# Performance

## Overview

Flaxon is designed to be performant for its intended use cases. It optimizes for I/O-bound workloads, not CPU-bound calculations.

## Performance Philosophy

"Fast" means measured low overhead for its intended workloads and efficient concurrency for I/O-bound applications — not an unqualified claim that Python is always faster than Node.js, Java, Go, or Rust.

## Optimization Areas

| Area | Optimization | Measurement |
|------|--------------|-------------|
| Routing | Precompiled patterns, radix/trie | Requests/second, latency |
| JSON | Compact encoding, optional faster serializer | Payload size, serialization time |
| Middleware | Avoid unnecessary wrappers | Per-layer microseconds |
| Validation | Cache schema metadata | Validation latency by payload |
| Templates | Cache compiled templates | Render latency, cache hit rate |
| WebSockets | Bound queues, efficient room lookup | Connections, messages/sec |

## Scaling Model

1. Keep HTTP workers stateless
2. Run more than one process for CPU and reliability
3. Place durable data in databases and files in object storage
4. Use Redis for caching, rate limits, sessions, and WebSocket fan-out
5. Move CPU-heavy jobs to workers or specialized services
6. Use a reverse proxy for TLS, limits, health checks, and rolling deployment

## Benchmarking

Flaxon includes benchmarks in the `benchmarks/` directory:

```bash
# Run all benchmarks
python scripts/benchmark.py

# Run specific benchmark
python benchmarks/routing_benchmark.py

Performance Tips
Use Async Where Possible
python
# Good
async def get_user(user_id: int):
    return await db.fetch_row("SELECT * FROM users WHERE id = $1", user_id)

# Avoid blocking
def get_user(user_id: int):
    return db.fetch_row_sync("SELECT * FROM users WHERE id = $1", user_id)
Use Connection Pooling
python
@app.on_startup
async def startup():
    app.state.db = await create_pool()

@app.get("/users")
async def get_users():
    async with app.state.db.acquire() as conn:
        return await conn.fetch("SELECT * FROM users")
Cache Frequently Accessed Data
python
from flaxon.caching import cached

@cached(ttl=60)
async def get_users():
    return await db.fetch_all("SELECT * FROM users")
Use Redis for Rate Limiting
python
from flaxon.security import DistributedRateLimiter

limiter = DistributedRateLimiter(redis_client)

@app.get("/api")
async def api(request):
    if not await limiter.check(request.client[0], requests=60):
        raise HTTPException(429, "Too many requests")
Realistic Goals
Flaxon should make Python suitable for many chat, social, dashboard, and mobile backends, while allowing high-load subsystems to use optimized services or other languages when evidence supports that choice.