from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from flaxon.http import StreamingResponse


class FileStreamer:
    def __init__(self, chunk_size: int = 8192) -> None:
        self.chunk_size = chunk_size

    async def stream_file(self, path: str) -> AsyncIterator[bytes]:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    async def stream_file_async(self, path: str) -> AsyncIterator[bytes]:
        try:
            import aiofiles
            async with aiofiles.open(path, "rb") as f:
                while True:
                    chunk = await f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except ImportError:
            async for chunk in self.stream_file(path):
                yield chunk

    def create_response(self, path: str, filename: str | None = None) -> StreamingResponse:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or "application/octet-stream"

        headers = {}
        if filename:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return StreamingResponse(
            self.stream_file(path),
            media_type=mime_type,
            headers=headers,
        )

    def create_response_async(self, path: str, filename: str | None = None) -> StreamingResponse:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or "application/octet-stream"

        headers = {}
        if filename:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return StreamingResponse(
            self.stream_file_async(path),
            media_type=mime_type,
            headers=headers,
        )

    def get_file_info(self, path: str) -> dict[str, str | int]:
        stat = os.stat(path)
        return {
            "size": stat.st_size,
            "mime_type": self._guess_mime_type(path),
            "filename": os.path.basename(path),
        }

    def _guess_mime_type(self, path: str) -> str:
        import mimetypes
        mime, _ = mimetypes.guess_type(path)
        return mime or "application/octet-stream"

    def is_path_safe(self, path: str, base_dir: str) -> bool:
        try:
            resolved_path = Path(path).resolve()
            resolved_base = Path(base_dir).resolve()
            return resolved_path.is_relative_to(resolved_base)
        except ValueError:
            return False
