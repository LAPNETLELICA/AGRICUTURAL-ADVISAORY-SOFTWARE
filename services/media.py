"""Controlled image-evidence lifecycle for V1.

Images remain evidence references only. No disease/pest classification is performed in V1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from uuid import uuid4

from sqlalchemy import select

from integrations.database.connection import Database
from integrations.database.tables import MediaEvidenceRow
from integrations.storage import ObjectStorage

_ALLOWED_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@dataclass(frozen=True, slots=True)
class MediaEvidence:
    image_id: str
    farmer_id: str
    crop_id: str | None
    request_id: str | None
    original_filename: str | None
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime
    expires_at: datetime


def _detected_mime(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


class MediaService:
    def __init__(
        self,
        storage: ObjectStorage,
        database: Database | None,
        *,
        max_bytes: int,
        retention_days: int,
    ) -> None:
        self._storage = storage
        self._database = database
        self._max_bytes = max_bytes
        self._retention_days = retention_days
        self._memory: dict[str, tuple[MediaEvidence, str]] = {}
        self._lock = RLock()

    def upload(
        self,
        *,
        farmer_id: str,
        content: bytes,
        mime_type: str,
        filename: str | None = None,
        crop_id: str | None = None,
        request_id: str | None = None,
    ) -> MediaEvidence:
        if not farmer_id:
            raise ValueError("farmer_id is required")
        if not content:
            raise ValueError("image is empty")
        if len(content) > self._max_bytes:
            raise ValueError(f"image exceeds maximum size of {self._max_bytes} bytes")
        supplied = mime_type.lower().split(";", 1)[0].strip()
        detected = _detected_mime(content)
        if supplied not in _ALLOWED_MIME or detected != supplied:
            raise ValueError("only valid JPEG, PNG, or WebP image evidence is accepted")

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self._retention_days)
        image_id = str(uuid4())
        extension = _ALLOWED_MIME[supplied]
        key = f"{now:%Y/%m}/{farmer_id}/{image_id}{extension}"
        stored = self._storage.put(key, content)
        safe_filename = Path(filename).name[:255] if filename else None
        evidence = MediaEvidence(
            image_id=image_id,
            farmer_id=farmer_id,
            crop_id=crop_id,
            request_id=request_id,
            original_filename=safe_filename,
            mime_type=supplied,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            created_at=now,
            expires_at=expires_at,
        )

        if self._database is None:
            with self._lock:
                self._memory[image_id] = (evidence, key)
            return evidence

        with self._database.sessions.begin() as session:
            session.add(
                MediaEvidenceRow(
                    image_id=image_id,
                    farmer_id=farmer_id,
                    crop_id=crop_id,
                    request_id=request_id,
                    storage_key=key,
                    original_filename=safe_filename,
                    mime_type=supplied,
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    created_at=now,
                    expires_at=expires_at,
                    deleted_at=None,
                )
            )
        return evidence

    def validate_references(self, farmer_id: str, image_ids: list[str]) -> None:
        for image_id in image_ids:
            try:
                item = self.metadata(image_id)
            except KeyError as exc:
                raise ValueError(f"image evidence not found: {image_id}") from exc
            if item.farmer_id != farmer_id:
                raise PermissionError(f"image evidence is not owned by farmer: {image_id}")
            if item.expires_at <= datetime.now(UTC):
                raise ValueError(f"image evidence expired: {image_id}")

    def get(self, image_id: str) -> tuple[MediaEvidence, bytes]:
        evidence, key = self._metadata_and_key(image_id)
        if evidence.expires_at <= datetime.now(UTC):
            raise KeyError(image_id)
        return evidence, self._storage.get(key)

    def metadata(self, image_id: str) -> MediaEvidence:
        evidence, _ = self._metadata_and_key(image_id)
        return evidence

    def delete(self, image_id: str) -> bool:
        if self._database is None:
            with self._lock:
                record = self._memory.pop(image_id, None)
            if record is None:
                return False
            self._storage.delete(record[1])
            return True

        with self._database.sessions.begin() as session:
            row = session.get(MediaEvidenceRow, image_id)
            if row is None or row.deleted_at is not None:
                return False
            self._storage.delete(row.storage_key)
            row.deleted_at = datetime.now(UTC)
        return True

    def list_for_farmer(self, farmer_id: str) -> list[MediaEvidence]:
        if self._database is None:
            with self._lock:
                values = [v[0] for v in self._memory.values() if v[0].farmer_id == farmer_id]
            return sorted(values, key=lambda item: item.created_at)

        statement = (
            select(MediaEvidenceRow)
            .where(MediaEvidenceRow.farmer_id == farmer_id, MediaEvidenceRow.deleted_at.is_(None))
            .order_by(MediaEvidenceRow.created_at)
        )
        with self._database.sessions() as session:
            return [self._from_row(row) for row in session.scalars(statement).all()]

    def purge_expired(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        if self._database is None:
            with self._lock:
                expired = [
                    image_id
                    for image_id, (evidence, _) in self._memory.items()
                    if evidence.expires_at <= moment
                ]
            for image_id in expired:
                self.delete(image_id)
            return len(expired)

        statement = select(MediaEvidenceRow).where(
            MediaEvidenceRow.expires_at <= moment,
            MediaEvidenceRow.deleted_at.is_(None),
        )
        count = 0
        with self._database.sessions.begin() as session:
            for row in session.scalars(statement).all():
                self._storage.delete(row.storage_key)
                row.deleted_at = moment
                count += 1
        return count

    def delete_farmer_media(self, farmer_id: str) -> int:
        items = self.list_for_farmer(farmer_id)
        return sum(1 for item in items if self.delete(item.image_id))

    def _metadata_and_key(self, image_id: str) -> tuple[MediaEvidence, str]:
        if self._database is None:
            with self._lock:
                record = self._memory.get(image_id)
            if record is None:
                raise KeyError(image_id)
            return record

        with self._database.sessions() as session:
            row = session.get(MediaEvidenceRow, image_id)
            if row is None or row.deleted_at is not None:
                raise KeyError(image_id)
            return self._from_row(row), row.storage_key

    @staticmethod
    def _from_row(row: MediaEvidenceRow) -> MediaEvidence:
        return MediaEvidence(
            image_id=row.image_id,
            farmer_id=row.farmer_id,
            crop_id=row.crop_id,
            request_id=row.request_id,
            original_filename=row.original_filename,
            mime_type=row.mime_type,
            size_bytes=row.size_bytes,
            sha256=row.sha256,
            created_at=row.created_at,
            expires_at=row.expires_at,
        )
