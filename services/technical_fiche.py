"""Sanitized, reviewable technical fiches derived from recommendations."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import TypeVar, overload
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


_T = TypeVar("_T")


@overload
def sanitize(value: Mapping[str, _T]) -> dict[str, _T]: ...


@overload
def sanitize(value: list[_T]) -> list[_T]: ...


@overload
def sanitize(value: _T) -> _T: ...


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
        self,
        *,
        owner_id: str,
        recommendation: Recommendation,
        subject: str,
        language: str,
        context: dict[str, object] | None = None,
        weather: dict[str, object] | None = None,
    ) -> TechnicalFiche:
        now = datetime.now(UTC)
        content = self._build_content(recommendation, subject, context or {}, weather or {})
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

    @staticmethod
    def _build_content(
        recommendation: Recommendation,
        subject: str,
        context: dict[str, object],
        weather: dict[str, object],
    ) -> dict[str, object]:
        general_information: dict[str, object] = {
            "title": recommendation.primary.name,
            "crop": recommendation.crop_id,
            "subject": subject,
        }
        for key in ("region", "locality", "plot", "surface_area", "variety", "stage"):
            if context.get(key):
                general_information[key] = context[key]

        content: dict[str, object] = {"general_information": general_information}
        intent = context.get("intent")
        if intent == "crop_problem":
            content["diagnosis"] = {
                "main_need": subject,
                "observations": context.get("symptoms") or recommendation.primary.summary,
                "objective": "Protect crop health and limit spread.",
            }

        actions = list(recommendation.actions)
        recommendations: dict[str, object] = {}
        if intent == "crop_problem":
            recommendations["crop_protection"] = actions
        elif intent == "start_farming":
            recommendations["cultural_practices"] = actions
        elif intent == "soil":
            recommendations["nutrition"] = actions
        elif actions:
            recommendations["technical_actions"] = actions
        if recommendations:
            content["recommendations"] = recommendations

        content["action_calendar"] = [
            {"action": action, "period": "À planifier", "status": "À planifier"}
            for action in actions
        ]
        safety: dict[str, object] = {"warnings": list(recommendation.warnings)}
        weather_advice = [
            str(value)
            for value in weather.values()
            if value
            and "unavailable" not in str(value).casefold()
            and "provider" not in str(value).casefold()
        ]
        if weather_advice:
            safety["weather"] = weather_advice
        content["safety"] = safety
        content["follow_up"] = {"next_step": "Review progress after the planned actions."}
        return content

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
