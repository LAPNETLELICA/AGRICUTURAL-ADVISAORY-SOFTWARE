"""Configurable profile context consumed by every client surface.

This deliberately describes presentation preferences only; it never changes the
agricultural conclusion produced by the advisory engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock

from integrations.database.connection import Database
from integrations.database.tables import UserProfileRow

LEVELS = ("beginner", "basic", "intermediate", "advanced")
VOCABULARY_LEVELS = ("simple", "standard", "technical")


@dataclass(frozen=True, slots=True)
class ApplicationProfile:
    user_id: str
    identity_type: str
    knowledge_level: str
    language: str
    vocabulary_level: str


class ApplicationContextService:
    def __init__(self, database: Database | None) -> None:
        self._database = database
        self._memory: dict[str, ApplicationProfile] = {}
        self._lock = RLock()

    def get(self, user_id: str) -> ApplicationProfile | None:
        if self._database is None:
            with self._lock:
                return self._memory.get(user_id)
        with self._database.sessions() as session:
            row = session.get(UserProfileRow, user_id)
            return self._from_row(row) if row else None

    def save(self, profile: ApplicationProfile) -> ApplicationProfile:
        self._validate(profile)
        if self._database is None:
            with self._lock:
                self._memory[profile.user_id] = profile
            return profile
        with self._database.sessions.begin() as session:
            session.merge(UserProfileRow(**asdict(profile), updated_at=datetime.now(UTC)))
        return profile

    def context(self, user_id: str) -> dict[str, object]:
        profile = self.get(user_id)
        return {
            "profile_complete": profile is not None,
            "profile": asdict(profile) if profile else None,
            "available_identity_types": "configurable",
            "available_knowledge_levels": list(LEVELS),
            "available_vocabulary_levels": list(VOCABULARY_LEVELS),
            "sections": ["recommendation", "education", "technical_fiches"] if profile else [],
            "presentation": (
                {
                    "language": profile.language,
                    "knowledge_level": profile.knowledge_level,
                    "vocabulary_level": profile.vocabulary_level,
                }
                if profile
                else None
            ),
        }

    @staticmethod
    def _validate(profile: ApplicationProfile) -> None:
        if not profile.identity_type:
            raise ValueError("identity_type is required")
        if profile.knowledge_level.lower() not in LEVELS:
            raise ValueError(f"knowledge_level must be one of: {', '.join(LEVELS)}")
        if profile.vocabulary_level.lower() not in VOCABULARY_LEVELS:
            raise ValueError(f"vocabulary_level must be one of: {', '.join(VOCABULARY_LEVELS)}")
        if not profile.language:
            raise ValueError("language is required")

    @staticmethod
    def _from_row(row: UserProfileRow) -> ApplicationProfile:
        return ApplicationProfile(
            user_id=row.user_id,
            identity_type=row.identity_type,
            knowledge_level=row.knowledge_level,
            language=row.language,
            vocabulary_level=row.vocabulary_level,
        )
