from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from .upload import UploadedFile


class FileStorage:
    def __init__(self, base_path: str = "uploads", url_prefix: str = "/uploads") -> None:
        self.base_path = Path(base_path)
        self.url_prefix = url_prefix
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, original_filename: str) -> str:
        ext = ""
        if "." in original_filename:
            ext = original_filename.rsplit(".", 1)[1]
            ext = f".{ext}" if ext else ""

        return f"{uuid.uuid4().hex}{ext}"

    def save(self, file: UploadedFile, path: str | None = None, filename: str | None = None) -> str:
        if filename is None:
            filename = self.generate_filename(file.filename)

        if path is None:
            path = ""

        full_path = self.base_path / path / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(full_path))
        return str(full_path)

    def save_bytes(self, data: bytes, filename: str, path: str | None = None) -> str:
        if path is None:
            path = ""

        full_path = self.base_path / path / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(data)

        return str(full_path)

    def delete(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except OSError:
            return False

    def delete_directory(self, directory: str) -> bool:
        try:
            path = self.base_path / directory
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
                return True
            return False
        except OSError:
            return False

    def exists(self, file_path: str) -> bool:
        return Path(file_path).exists()

    def get_size(self, file_path: str) -> int:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size
        return 0

    def get_url(self, file_path: str) -> str:
        relative = Path(file_path).relative_to(self.base_path)
        return f"{self.url_prefix}/{relative}"

    def list_files(self, directory: str = "") -> list[str]:
        path = self.base_path / directory
        if not path.exists():
            return []

        return [str(p) for p in path.iterdir() if p.is_file()]

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {}

        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "path": str(path),
            "extension": path.suffix,
        }
