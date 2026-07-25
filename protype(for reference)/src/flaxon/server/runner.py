from __future__ import annotations

from typing import Any


def run(app: Any, *, host: str = "127.0.0.1", port: int = 8000, reload: bool = False, workers: int = 1) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Uvicorn is required. Install flaxon-framework[server].") from exc
    uvicorn.run(app, host=host, port=port, reload=reload, workers=workers)
