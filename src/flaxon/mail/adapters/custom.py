from __future__ import annotations

from typing import Any


class CustomAdapter:
    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    async def send(self, email: Any) -> None:
        if hasattr(self.adapter, "send"):
            result = self.adapter.send(email)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Adapter does not support send")
