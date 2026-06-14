"""Object storage abstraction.

MVP uses the local filesystem with randomized keys. The interface is small so a
later S3-compatible backend can drop in without touching callers.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from .config import get_settings


class LocalStorage:
    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, original_filename: str) -> str:
        """Store bytes under a randomized key; return the storage key."""
        suffix = Path(os.path.basename(original_filename)).suffix.lower()
        key = f"{uuid.uuid4().hex}{suffix}"
        (self.base / key).write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        # basename guards against path traversal via a crafted key.
        safe = os.path.basename(key)
        return (self.base / safe).read_bytes()

    def path(self, key: str) -> Path:
        return self.base / os.path.basename(key)


def get_storage() -> LocalStorage:
    return LocalStorage(get_settings().storage_dir)
