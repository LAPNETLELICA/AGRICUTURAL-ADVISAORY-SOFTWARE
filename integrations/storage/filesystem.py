"""Private local filesystem storage for V1/development.

Files are stored outside static web roots and can only be retrieved through the
authenticated media API. The ObjectStorage protocol allows an S3/MinIO adapter to
replace this implementation later without changing the API/service layer.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from integrations.storage.protocols import StoredObject


class PrivateFilesystemStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self._root / key).resolve()
        if self._root != candidate and self._root not in candidate.parents:
            raise ValueError("invalid storage key")
        return candidate

    def put(self, key: str, content: bytes) -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
        return StoredObject(
            key=key,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()
