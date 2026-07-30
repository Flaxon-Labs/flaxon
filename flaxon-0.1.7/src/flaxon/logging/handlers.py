from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler as BaseRotatingFileHandler
from typing import Any


class ConsoleHandler(logging.StreamHandler):
    def __init__(self, stream: Any = None) -> None:
        if stream is None:
            stream = sys.stdout
        super().__init__(stream)


class FileHandler(logging.FileHandler):
    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8") -> None:
        super().__init__(filename, mode, encoding)


class RotatingFileHandler(BaseRotatingFileHandler):
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10485760,
        backup_count: int = 5,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(filename, max_bytes, backup_count, encoding)


class SyslogHandler(logging.handlers.SysLogHandler):
    def __init__(
        self,
        address: tuple[str, int] | str = ("localhost", 514),
        facility: int = logging.handlers.SysLogHandler.LOG_USER,
        socktype: int | None = None,
    ) -> None:
        super().__init__(address, facility, socktype)


class NullHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        pass


class MemoryHandler(logging.handlers.MemoryHandler):
    def __init__(self, capacity: int = 100, target: logging.Handler | None = None) -> None:
        super().__init__(capacity, target=target)


class HTTPHandler(logging.handlers.HTTPHandler):
    def __init__(self, host: str, url: str, method: str = "POST", secure: bool = False) -> None:
        super().__init__(host, url, method, secure)


def create_handler(
    handler_type: str,
    **kwargs: Any,
) -> logging.Handler:
    handlers = {
        "console": ConsoleHandler,
        "file": FileHandler,
        "rotating_file": RotatingFileHandler,
        "syslog": SyslogHandler,
        "null": NullHandler,
        "memory": MemoryHandler,
        "http": HTTPHandler,
    }

    handler_class = handlers.get(handler_type)
    if handler_class is None:
        raise ValueError(f"Unknown handler type: {handler_type}")

    return handler_class(**kwargs)
