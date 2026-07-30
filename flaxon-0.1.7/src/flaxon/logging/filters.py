from __future__ import annotations

import logging
import re


class Filter:
    def __init__(self, name: str) -> None:
        self.name = name

    def filter(self, record: logging.LogRecord) -> bool:
        return True


class LevelFilter(Filter):
    def __init__(self, name: str, min_level: int, max_level: int | None = None) -> None:
        super().__init__(name)
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < self.min_level:
            return False
        if self.max_level is not None and record.levelno > self.max_level:
            return False
        return True


class RequestFilter(Filter):
    def __init__(self, name: str, path_pattern: str | None = None, method: str | None = None) -> None:
        super().__init__(name)
        self.path_pattern = re.compile(path_pattern) if path_pattern else None
        self.method = method.upper() if method else None

    def filter(self, record: logging.LogRecord) -> bool:
        path = getattr(record, "path", None)
        method = getattr(record, "method", None)

        if self.path_pattern and path:
            if not self.path_pattern.search(path):
                return False

        if self.method and method:
            if method.upper() != self.method:
                return False

        return True


class ModuleFilter(Filter):
    def __init__(self, name: str, modules: list[str]) -> None:
        super().__init__(name)
        self.modules = modules

    def filter(self, record: logging.LogRecord) -> bool:
        return record.module in self.modules


class ExcludeModuleFilter(Filter):
    def __init__(self, name: str, modules: list[str]) -> None:
        super().__init__(name)
        self.modules = modules

    def filter(self, record: logging.LogRecord) -> bool:
        return record.module not in self.modules


class UserFilter(Filter):
    def __init__(self, name: str, user_ids: list[str | int]) -> None:
        super().__init__(name)
        self.user_ids = {str(uid) for uid in user_ids}

    def filter(self, record: logging.LogRecord) -> bool:
        user_id = getattr(record, "user_id", None)
        if user_id is None:
            return False
        return str(user_id) in self.user_ids


class RequestIDFilter(Filter):
    def __init__(self, name: str, request_id: str) -> None:
        super().__init__(name)
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        rid = getattr(record, "request_id", None)
        return rid == self.request_id


class StatusFilter(Filter):
    def __init__(self, name: str, statuses: list[int]) -> None:
        super().__init__(name)
        self.statuses = set(statuses)

    def filter(self, record: logging.LogRecord) -> bool:
        status = getattr(record, "status", None)
        return status in self.statuses


def add_filter(logger: logging.Logger, filter_obj: Filter) -> None:
    logger.addFilter(filter_obj)


def remove_filter(logger: logging.Logger, filter_obj: Filter) -> None:
    logger.removeFilter(filter_obj)
