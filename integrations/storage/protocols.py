"""Provider-neutral object storage contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size_bytes: int
    sha256: str


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes) -> StoredObject: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...
