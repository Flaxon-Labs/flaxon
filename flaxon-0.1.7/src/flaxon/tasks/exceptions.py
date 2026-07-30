from __future__ import annotations

from flaxon.exceptions import FlaxonError


class TaskError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class TaskNotFoundError(TaskError):
    def __init__(self, message: str = "Task not found") -> None:
        super().__init__(message)


class TaskQueueError(TaskError):
    def __init__(self, message: str = "Task queue error") -> None:
        super().__init__(message)


class TaskResultError(TaskError):
    def __init__(self, message: str = "Task result error") -> None:
        super().__init__(message)


class TaskTimeoutError(TaskError):
    def __init__(self, message: str = "Task timed out") -> None:
        super().__init__(message)


class TaskRegistrationError(TaskError):
    def __init__(self, message: str = "Task registration error") -> None:
        super().__init__(message)


class TaskExecutionError(TaskError):
    def __init__(self, message: str = "Task execution error") -> None:
        super().__init__(message)
