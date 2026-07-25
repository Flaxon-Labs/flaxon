from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any


def _coerce(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    if "," in value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Config(dict[str, Any]):
    DEFAULTS = {
        "ENV": "development",
        "DEBUG": False,
        "SECRET_KEY": None,
        "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
        "MAX_BODY_SIZE": 10 * 1024 * 1024,
    }

    def __init__(self, values: Mapping[str, Any] | None = None, *, prefix: str = "FLAXON_") -> None:
        super().__init__(self.DEFAULTS)
        self.update(values or {})
        for key, value in os.environ.items():
            if key.startswith(prefix):
                self[key[len(prefix):]] = _coerce(value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc
