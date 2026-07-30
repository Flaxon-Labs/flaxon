from __future__ import annotations

from typing import Any


class CustomStorageAdapter:
    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    async def write(self, path: str, data: bytes) -> None:
        if hasattr(self.adapter, "write"):
            result = self.adapter.write(path, data)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Adapter does not support write")

    async def read(self, path: str) -> bytes:
        if hasattr(self.adapter, "read"):
            result = self.adapter.read(path)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Adapter does not support read")

    async def delete(self, path: str) -> bool:
        if hasattr(self.adapter, "delete"):
            result = self.adapter.delete(path)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Adapter does not support delete")

    async def exists(self, path: str) -> bool:
        if hasattr(self.adapter, "exists"):
            result = self.adapter.exists(path)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Adapter does not support exists")

    async def size(self, path: str) -> int:
        if hasattr(self.adapter, "size"):
            result = self.adapter.size(path)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Adapter does not support size")

    async def list(self, path: str = "") -> list[str]:
        if hasattr(self.adapter, "list"):
            result = self.adapter.list(path)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Adapter does not support list")

    async def move(self, source: str, destination: str) -> None:
        if hasattr(self.adapter, "move"):
            result = self.adapter.move(source, destination)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Adapter does not support move")

    async def copy(self, source: str, destination: str) -> None:
        if hasattr(self.adapter, "copy"):
            result = self.adapter.copy(source, destination)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Adapter does not support copy")

    def get_url(self, path: str) -> str:
        if hasattr(self.adapter, "get_url"):
            return self.adapter.get_url(path)
        return f"/uploads/{path}"
