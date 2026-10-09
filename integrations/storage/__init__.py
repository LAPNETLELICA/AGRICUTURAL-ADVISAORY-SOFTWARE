"""Private object-storage boundary for farmer evidence."""

from integrations.storage.filesystem import PrivateFilesystemStorage
from integrations.storage.protocols import ObjectStorage, StoredObject

__all__ = ["ObjectStorage", "PrivateFilesystemStorage", "StoredObject"]
