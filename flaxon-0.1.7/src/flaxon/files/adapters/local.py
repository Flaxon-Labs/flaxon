from __future__ import annotations

import shutil
from pathlib import Path


class LocalStorageAdapter:
    def __init__(self, base_path: str = "uploads") -> None:
        self.base_path = Path(base_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        return self.base_path / path

    def write(self, path: str, data: bytes) -> None:
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)

    def read(self, path: str) -> bytes:
        full_path = self._get_full_path(path)
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        return self._get_full_path(path).exists()

    def size(self, path: str) -> int:
        full_path = self._get_full_path(path)
        if full_path.exists():
            return full_path.stat().st_size
        return 0

    def list(self, path: str = "") -> list[str]:
        full_path = self.base_path / path
        if not full_path.exists():
            return []

        result = []
        for item in full_path.iterdir():
            rel_path = str(item.relative_to(self.base_path))
            result.append(rel_path)
        return result

    def move(self, source: str, destination: str) -> None:
        src_path = self._get_full_path(source)
        dst_path = self._get_full_path(destination)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))

    def copy(self, source: str, destination: str) -> None:
        src_path = self._get_full_path(source)
        dst_path = self._get_full_path(destination)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(dst_path))

    def get_url(self, path: str, base_url: str = "/uploads") -> str:
        return f"{base_url}/{path}"
