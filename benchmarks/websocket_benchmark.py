#!/usr/bin/env python
"""
WebSocket performance benchmarks.
"""

import asyncio
import json
import time
from typing import Any

from flaxon import Flaxon
from flaxon.testing import AsyncWebSocketClient
from flaxon.websocket import WebSocket


def create_websocket_app() -> Flaxon:
    """Create a WebSocket app for benchmarking."""
    app = Flaxon("test-ws")

    @app.websocket("/ws/echo")
    async def echo(socket: WebSocket):
        await socket.accept()
        try:
            async for message in socket.iter_json():
                await socket.send_json({"echo": message})
        except Exception:
            pass

    @app.websocket("/ws/broadcast/<room_id>")
    async def broadcast(socket: WebSocket, room_id: str):
        await socket.accept()
        await socket.join(room_id)
        try:
            async for message in socket.iter_json():
                await socket.broadcast_json(room_id, message)
        finally:
            await socket.leave(room_id)

    return app


def benchmark_websocket_connection() -> dict[str, Any]:
    """Benchmark WebSocket connection establishment."""
    app = create_websocket_app()

    async def run():
        start = time.perf_counter()

        clients = []
        for i in range(100):
            client = AsyncWebSocketClient(app)
            await client.connect("/ws/echo")
            clients.append(client)

        elapsed = time.perf_counter() - start

        for client in clients:
            await client.disconnect()

        return elapsed

    elapsed = asyncio.run(run())

    return {
        "name": "WebSocket Connections",
        "connections": 100,
        "time_seconds": round(elapsed, 4),
        "connections_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_websocket_messages() -> dict[str, Any]:
    """Benchmark WebSocket message throughput."""
    app = create_websocket_app()

    async def run():
        client = AsyncWebSocketClient(app)
        await client.connect("/ws/echo")

        start = time.perf_counter()

        for i in range(100):
            await client.send_json({"message": f"Message {i}"})
            await client.receive_json()

        elapsed = time.perf_counter() - start

        await client.disconnect()
        return elapsed, 100

    elapsed, count = asyncio.run(run())

    return {
        "name": "WebSocket Messages (Echo)",
        "messages": count,
        "time_seconds": round(elapsed, 4),
        "messages_per_second": round(count / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_websocket_broadcast() -> dict[str, Any]:
    """Benchmark WebSocket broadcast performance."""
    app = create_websocket_app()

    async def run():
        clients = []
        for i in range(10):
            client = AsyncWebSocketClient(app)
            await client.connect("/ws/broadcast/room1")
            clients.append(client)

        sender = AsyncWebSocketClient(app)
        await sender.connect("/ws/broadcast/room1")

        start = time.perf_counter()

        for i in range(50):
            await sender.send_json({"message": f"Broadcast {i}"})
            for client in clients:
                await client.receive_json()

        elapsed = time.perf_counter() - start

        await sender.disconnect()
        for client in clients:
            await client.disconnect()

        return elapsed, 10 * 50

    elapsed, messages = asyncio.run(run())

    return {
        "name": "WebSocket Broadcast",
        "clients": 10,
        "messages": messages,
        "time_seconds": round(elapsed, 4),
        "messages_per_second": round(messages / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_websocket_concurrent() -> dict[str, Any]:
    """Benchmark concurrent WebSocket connections."""
    app = create_websocket_app()

    async def run():
        async def connect_and_echo():
            client = AsyncWebSocketClient(app)
            await client.connect("/ws/echo")
            await client.send_json({"ping": "ping"})
            await client.receive_json()
            await client.disconnect()

        start = time.perf_counter()

        tasks = [connect_and_echo() for _ in range(50)]
        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start
        return elapsed

    elapsed = asyncio.run(run())

    return {
        "name": "Concurrent WebSocket Connections",
        "connections": 50,
        "time_seconds": round(elapsed, 4),
        "connections_per_second": round(50 / elapsed, 0) if elapsed > 0 else 0,
    }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all WebSocket benchmarks."""
    results = [
        benchmark_websocket_connection(),
        benchmark_websocket_messages(),
        benchmark_websocket_broadcast(),
        benchmark_websocket_concurrent(),
    ]
    return results


def main() -> None:
    """Run and display benchmarks."""
    print("=" * 60)
    print("Flaxon WebSocket Benchmarks")
    print("=" * 60)

    results = run_benchmarks()

    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Time: {result['time_seconds']}s")
        for key, value in result.items():
            if key not in ["name", "time_seconds"]:
                print(f"  {key}: {value}")

    import os
    os.makedirs("benchmarks/results", exist_ok=True)

    with open("benchmarks/results/websocket_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/results/websocket_benchmark.json")


if __name__ == "__main__":
    main()