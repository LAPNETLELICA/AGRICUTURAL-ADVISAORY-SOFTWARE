"""Sanitized, reviewable technical fiches derived from recommendations."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from engine.models.responses import Recommendation
from integrations.database.connection import Database
from integrations.database.tables import TechnicalFicheRow

_PRIVATE_KEYS = re.compile(
    r"(?:name|phone|email|password|token|account|device|farmer_id|user_id)", re.I
)


@dataclass(frozen=True, slots=True)
class TechnicalFiche:
    fiche_id: str
    owner_id: str
    status: str
    crop_id: str | None
    subject: str
    language: str
    content: dict[str, object]
    created_at: datetime
    updated_at: datetime


def sanitize(value: object) -> object:
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items() if not _PRIVATE_KEYS.search(key)}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


class TechnicalFicheService:
    def __init__(self, database: Database | None) -> None:
        self._database = database
        self._memory: dict[str, TechnicalFiche] = {}
        self._lock = RLock()

    def from_recommendation(
        self, *, owner_id: str, recommendation: Recommendation, subject: str, language: str
    ) -> TechnicalFiche:
        now = datetime.now(UTC)
        content = {
            "title": recommendation.primary.name,
            "crop": recommendation.crop_id,
            "subject": subject,
            "observed_situation": recommendation.primary.summary,
            "possible_causes": recommendation.reasons,
            "recommendation": recommendation.primary.summary,
            "recommended_actions": recommendation.actions,
            "precautions": recommendation.warnings,
            "references": recommendation.rule_references,
            "visual_evidence_summary": None,
        }
        fiche = TechnicalFiche(
            fiche_id=str(uuid4()),
            owner_id=owner_id,
            status="DRAFT",
            crop_id=recommendation.crop_id,
            subject=subject,
            language=language,
            content=sanitize(content),
            created_at=now,
            updated_at=now,
        )
        return self._save(fiche)

    def get(self, fiche_id: str) -> TechnicalFiche | None:
        if self._database is None:
            with self._lock:
                return self._memory.get(fiche_id)
        with self._database.sessions() as session:
            row = session.get(TechnicalFicheRow, fiche_id)
            return self._from_row(row) if row else None

    def list_published(
        self, *, crop_id: str | None = None, subject: str | None = None
    ) -> list[TechnicalFiche]:
        fiches = self._all()
        return [
            f
            for f in fiches
            if f.status == "PUBLISHED"
            and (not crop_id or f.crop_id == crop_id)
            and (not subject or f.subject == subject)
        ]

    def set_status(self, fiche_id: str, status: str) -> TechnicalFiche:
        if status not in {"DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED"}:
            raise ValueError("invalid fiche status")
        fiche = self.get(fiche_id)
        if fiche is None:
            raise KeyError(fiche_id)
        return self._save(
            TechnicalFiche(**{**asdict(fiche), "status": status, "updated_at": datetime.now(UTC)})
        )

    def _all(self) -> list[TechnicalFiche]:
        if self._database is None:
            with self._lock:
                return list(self._memory.values())
        with self._database.sessions() as session:
            return [self._from_row(row) for row in session.query(TechnicalFicheRow).all()]

    def _save(self, fiche: TechnicalFiche) -> TechnicalFiche:
        if self._database is None:
            with self._lock:
                self._memory[fiche.fiche_id] = fiche
            return fiche
        with self._database.sessions.begin() as session:
            session.merge(TechnicalFicheRow(**asdict(fiche)))
        return fiche

    @staticmethod
    def _from_row(row: TechnicalFicheRow) -> TechnicalFiche:
        return TechnicalFiche(
            fiche_id=row.fiche_id,
            owner_id=row.owner_id,
            status=row.status,
            crop_id=row.crop_id,
            subject=row.subject,
            language=row.language,
            content=deepcopy(row.content),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
