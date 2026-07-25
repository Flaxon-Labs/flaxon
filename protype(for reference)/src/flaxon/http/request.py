from __future__ import annotations

import json
from http.cookies import SimpleCookie
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs

from flaxon.exceptions import HTTPException


class Headers(dict[str, str]):
    def __init__(self, raw: list[tuple[bytes, bytes]] | None = None) -> None:
        super().__init__()
        for key, value in raw or []:
            self[key.decode("latin-1").lower()] = value.decode("latin-1")


class Request:
    def __init__(self, scope: dict[str, Any], receive: Any, app: Any) -> None:
        self.scope = scope
        self._receive = receive
        self.app = app
        self.method = scope.get("method", "GET").upper()
        self.path = scope.get("path", "/")
        self.root_path = scope.get("root_path", "")
        self.scheme = scope.get("scheme", "http")
        self.headers = Headers(scope.get("headers", []))
        self.path_params: dict[str, Any] = scope.setdefault("path_params", {})
        self.state = SimpleNamespace()
        self.user: Any = None
        self._body: bytes | None = None

    @property
    def query(self) -> dict[str, str | list[str]]:
        raw = self.scope.get("query_string", b"").decode("utf-8")
        parsed = parse_qs(raw, keep_blank_values=True)
        return {key: values[0] if len(values) == 1 else values for key, values in parsed.items()}

    @property
    def cookies(self) -> dict[str, str]:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("cookie", ""))
        return {key: morsel.value for key, morsel in cookie.items()}

    @property
    def client(self) -> tuple[str, int] | None:
        return self.scope.get("client")

    @property
    def url(self) -> str:
        host = self.headers.get("host", "localhost")
        query = self.scope.get("query_string", b"").decode("utf-8")
        suffix = f"?{query}" if query else ""
        return f"{self.scheme}://{host}{self.root_path}{self.path}{suffix}"

    async def body(self) -> bytes:
        if self._body is not None:
            return self._body
        chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await self._receive()
            if message["type"] == "http.disconnect":
                break
            if message["type"] != "http.request":
                continue
            chunks.append(message.get("body", b""))
            more_body = bool(message.get("more_body", False))
        self._body = b"".join(chunks)
        return self._body

    async def json(self) -> Any:
        body = await self.body()
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "The request body contains invalid JSON.", code="FX-REQ-JSON") from exc

    async def text(self) -> str:
        return (await self.body()).decode("utf-8")

    async def render(self, template_name: str, context: dict[str, Any] | None = None, *, status_code: int = 200):
        if self.app.jinax is None:
            raise RuntimeError("Jinax is not configured for this application.")
        values = dict(context or {})
        values.setdefault("request", self)
        return await self.app.jinax.render_response(template_name, values, status_code=status_code)
