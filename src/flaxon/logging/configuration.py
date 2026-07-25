from __future__ import annotations

import logging
import os
from typing import Any


class LoggingConfig:
    DEFAULTS = {
        "level": logging.INFO,
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
        "propagate": False,
        "handlers": [],
    }

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = {**self.DEFAULTS, **(config or {})}
        self._load_env()

    def _load_env(self) -> None:
        log_level = os.environ.get("LOG_LEVEL", "").upper()
        if log_level:
            level = getattr(logging, log_level, None)
            if level is not None:
                self._config["level"] = level

        log_format = os.environ.get("LOG_FORMAT")
        if log_format:
            self._config["format"] = log_format

        log_file = os.environ.get("LOG_FILE")
        if log_file:
            self._config["handlers"].append({
                "type": "rotating_file",
                "filename": log_file,
            })

    @property
    def level(self) -> int:
        return self._config["level"]

    @level.setter
    def level(self, value: int) -> None:
        self._config["level"] = value

    @property
    def format(self) -> str:
        return self._config["format"]

    @property
    def datefmt(self) -> str:
        return self._config["datefmt"]

    @property
    def propagate(self) -> bool:
        return self._config["propagate"]

    @property
    def handlers(self) -> list[dict[str, Any]]:
        return self._config["handlers"]

    def add_handler(self, handler: dict[str, Any]) -> None:
        self._config["handlers"].append(handler)

    def add_console_handler(self, level: int | None = None, formatter: str = "console") -> None:
        handler = {"type": "console", "formatter": formatter}
        if level is not None:
            handler["level"] = level
        self._config["handlers"].append(handler)

    def add_file_handler(self, filename: str, level: int | None = None, formatter: str = "console") -> None:
        handler = {"type": "file", "filename": filename, "formatter": formatter}
        if level is not None:
            handler["level"] = level
        self._config["handlers"].append(handler)

    def add_rotating_file_handler(
        self,
        filename: str,
        max_bytes: int = 10485760,
        backup_count: int = 5,
        level: int | None = None,
        formatter: str = "console",
    ) -> None:
        handler = {
            "type": "rotating_file",
            "filename": filename,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
            "formatter": formatter,
        }
        if level is not None:
            handler["level"] = level
        self._config["handlers"].append(handler)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._config)
