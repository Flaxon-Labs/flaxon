from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, AsyncIterator, Iterable


class FlaxonJSONEncoder(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if hasattr(value, "to_dict"):
            return value.to_dict()
        return super().default(value)


class Response:
    media_type = "text/plain; charset=utf-8"

    def __init__(
        self,
        content: bytes | str = b"",
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.media_type = media_type or self.media_type
        self.body = content.encode("utf-8") if isinstance(content, str) else content
        self.headers.setdefault("content-type", self.media_type)
        self.headers.setdefault("content-length", str(len(self.body)))

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        raw_headers = [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in self.headers.items()]
        await send({"type": "http.response.start", "status": self.status_code, "headers": raw_headers})
        await send({"type": "http.response.body", "body": self.body, "more_body": False})

    @classmethod
    def from_value(cls, value: Any) -> "Response":
        if isinstance(value, Response):
            return value
        if value is None:
            return Response(b"", status_code=204)
        if isinstance(value, (dict, list, tuple)) or is_dataclass(value):
            return JSONResponse(value)
        if isinstance(value, bytes):
            return Response(value, media_type="application/octet-stream")
        return TextResponse(str(value))


class JSONResponse(Response):
    media_type = "application/json; charset=utf-8"

    def __init__(
        self,
        content: Any,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(content, cls=FlaxonJSONEncoder, ensure_ascii=False, separators=(",", ":"))
        super().__init__(body, status_code=status_code, headers=headers, media_type=self.media_type)


class HTMLResponse(Response):
    media_type = "text/html; charset=utf-8"


class TextResponse(Response):
    media_type = "text/plain; charset=utf-8"


class RedirectResponse(Response):
    def __init__(self, url: str, status_code: int = 307, headers: dict[str, str] | None = None) -> None:
        merged = dict(headers or {})
        merged["location"] = url
        super().__init__(b"", status_code=status_code, headers=merged)


class StreamingResponse(Response):
    def __init__(
        self,
        content: AsyncIterator[bytes] | Iterable[bytes],
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/octet-stream",
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.media_type = media_type
        self.headers.setdefault("content-type", media_type)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        raw_headers = [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in self.headers.items()]
        await send({"type": "http.response.start", "status": self.status_code, "headers": raw_headers})
        if hasattr(self.content, "__aiter__"):
            async for chunk in self.content:  # type: ignore[union-attr]
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        else:
            for chunk in self.content:  # type: ignore[union-attr]
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
        await send({"type": "http.response.body", "body": b"", "more_body": False})
