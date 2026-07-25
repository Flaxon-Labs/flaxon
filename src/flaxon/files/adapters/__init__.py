from __future__ import annotations

from .custom import CustomStorageAdapter
from .local import LocalStorageAdapter
from .s3 import S3StorageAdapter

__all__ = [
    "CustomStorageAdapter",
    "LocalStorageAdapter",
    "S3StorageAdapter",
]
