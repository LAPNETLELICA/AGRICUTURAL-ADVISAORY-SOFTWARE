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

from engine.models.responses import Recommendation, TraceRecord
from integrations.database.connection import Database
from integrations.database.tables import TechnicalFicheRow
from services.application_context import ApplicationProfile

_PRIVATE_KEYS = re.compile(
    r"(?:name|phone|email|password|token|account|device|farmer_id|user_id)", re.I
)
_INTERNAL_TEXT = re.compile(
    r"provider unavailable|weather data is unavailable|traceback|stack trace|"
    r"api\.openweathermap\.org|"
    r"https?://[^\s]*(?:api|internal)|(?:/app/|/home/)[^\s]*\.py|"
    r"\b(?:keyerror|typeerror|runtimeerror|connectionerror|timeouterror)\b",
    re.I,
)


def _safe_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or _INTERNAL_TEXT.search(value):
        return None
    return value.strip()


def _safe_items(values: list[str]) -> list[str]:
    return [safe for value in values if (safe := _safe_text(value)) is not None]


def _locale(language: str) -> dict[str, str]:
    base = language.split("-", 1)[0].split("_", 1)[0].lower()
    if base in {"en", "fr"}:
        return {"requested": language, "rendered": base}
    return {
        "requested": language,
        "rendered": "en",
        "fallback_note": "English labels are used because the selected language is not supported.",
    }


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
        trace: TraceRecord | None = None,
        profile: ApplicationProfile | None = None,
    ) -> TechnicalFiche:
        for existing in self._all():
            cover = existing.content.get("cover")
            if (
                existing.owner_id == owner_id
                and existing.subject == subject
                and existing.language == language
                and isinstance(cover, dict)
                and cover.get("recommendation_id") == recommendation.recommendation_id
            ):
                return existing
        now = datetime.now(UTC)
        content = self._build_content(
            recommendation, subject, context or {}, weather or {}, trace, profile, language, now
        )
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
        trace: TraceRecord | None,
        profile: ApplicationProfile | None,
        language: str,
        generated_at: datetime,
    ) -> dict[str, object]:
        present = trace.present_conditions_used if trace else {}
        future = trace.future_conditions_used if trace else {}
        trace_context = trace.context_used if trace else {}
        question = _safe_text(context.get("question")) or _safe_text(present.get("question"))
        selected_actions = _safe_items(recommendation.actions)
        selected_reasons = _safe_items(recommendation.reasons)
        selected_warnings = _safe_items(recommendation.warnings)
        selected_uncertainty = _safe_items(recommendation.uncertainty)
        rule_sources: list[dict[str, str]] = []
        if trace:
            for evaluation in trace.evaluated_rules:
                candidate = evaluation.candidate
                if candidate is None or evaluation.rule_id not in recommendation.rule_references:
                    continue
                source = candidate.source
                rule_sources.append(
                    {
                        "rule_id": evaluation.rule_id,
                        "title": source.title,
                        "status": candidate.rule_status.value,
                        **({"uri": source.uri} if source.uri else {}),
                    }
                )
        is_validated = bool(rule_sources) and all(
            item["status"] == "validated" for item in rule_sources
        )
        is_validated = is_validated and recommendation.primary.name != "insufficient_evidence"
        validation_status = "validated" if is_validated else "preliminary"
        language_info = _locale(language or (profile.language if profile else "en"))

        farm_context: dict[str, object] = {"crop": recommendation.crop_id}
        for name, value in (
            ("region", trace_context.get("region") or context.get("region")),
            ("locality", trace_context.get("locality") or context.get("locality")),
            ("variety", context.get("variety")),
            ("surface_area", context.get("surface_area")),
            ("stage", present.get("current_stage") or context.get("stage")),
            ("season", future.get("cultivation_period") or context.get("cultivation_period")),
        ):
            if isinstance(value, (str, int, float)) and value != "":
                farm_context[name] = value
        for category, names in (
            ("soil", ("type", "ph", "drainage")),
            ("topography", ("landform", "altitude_m")),
            ("practices", ("irrigation", "cultivation")),
        ):
            facts = present.get(category)
            if isinstance(facts, dict):
                selected = {key: facts[key] for key in names if facts.get(key) is not None}
                if selected:
                    farm_context[category] = selected

        observed = present.get("observations")
        diagnosis: dict[str, object] = {"reported_problem": question or subject}
        if context.get("symptoms"):
            diagnosis["observations"] = context["symptoms"]
        elif isinstance(observed, dict):
            observations = {
                key: observed[key] for key in ("symptom", "symptoms", "issue") if observed.get(key)
            }
            if observations:
                diagnosis["observations"] = observations
        if selected_reasons:
            diagnosis["engine_findings"] = selected_reasons
        if context.get("intent") == "crop_problem":
            diagnosis["main_need"] = subject
        if selected_uncertainty:
            diagnosis["missing_or_uncertain"] = selected_uncertainty
        if recommendation.alternatives:
            diagnosis["alternative_explanations"] = [
                item.summary for item in recommendation.alternatives if _safe_text(item.summary)
            ]

        recommendations: dict[str, object] = {
            "primary": recommendation.primary.name,
            "summary": recommendation.primary.summary,
            "steps": selected_actions,
        }
        if recommendation.primary.name == "insufficient_evidence":
            recommendations["limitations"] = (
                "Insufficient evidence for a crop treatment; provide more observations "
                "or request a qualified field assessment."
            )
        if selected_reasons:
            recommendations["reasons"] = selected_reasons
        if recommendation.action_guidance:
            recommendations["guidance"] = [
                {
                    "action": guidance.action,
                    "materials": _safe_items(guidance.recommended_materials),
                    "application_steps": _safe_items(guidance.application_steps),
                }
                for guidance in recommendation.action_guidance
                if _safe_text(guidance.action)
            ]
        if selected_warnings:
            recommendations["warnings"] = selected_warnings
        intent = context.get("intent")
        legacy_action_key = {
            "crop_problem": "crop_protection",
            "start_farming": "cultural_practices",
            "soil": "nutrition",
        }.get(intent if isinstance(intent, str) else "", "technical_actions")
        if selected_actions:
            recommendations[legacy_action_key] = selected_actions

        cover: dict[str, object] = {
            "title": "Agricultural Technical File",
            "crop": recommendation.crop_id,
            "subject": subject,
            "recommendation_id": recommendation.recommendation_id,
            "generated_at": generated_at.isoformat(),
            "validation_status": validation_status,
        }
        for key in ("region", "locality"):
            if key in farm_context:
                cover[key] = farm_context[key]

        executive_summary: dict[str, object] = {
            "reported_objective": question or subject,
            "finding": recommendation.primary.summary,
            "principal_action": recommendation.primary.name,
        }
        if selected_actions:
            executive_summary["first_step"] = selected_actions[0]

        selected_weather: list[str] = []
        forecast = future.get("weather")
        for data, label in (
            (present.get("weather"), "Current"),
            (forecast, "Forecast"),
            (weather, "Forecast"),
        ):
            if not isinstance(data, dict):
                continue
            for key, suffix in (
                ("condition", ""),
                ("rainfall_class", "rainfall class"),
                ("rainfall_mm", "mm rainfall"),
                ("warning", "warning"),
            ):
                value = data.get(key)
                if isinstance(value, (str, int, float)) and (safe := _safe_text(str(value))):
                    item = f"{label} {suffix}: {safe}" if suffix else f"{label}: {safe}"
                    if item not in selected_weather:
                        selected_weather.append(item)
        if selected_weather:
            farm_context["weather"] = selected_weather

        action_calendar = [
            {
                "action": action,
                "instructions": action,
                "period": "Not provided",
                "materials": [],
                "status": "À planifier",
            }
            for action in selected_actions
        ]
        monitoring: dict[str, object] = {
            "checklist": ["Record what changes in the crop before requesting follow-up advice."],
            "follow_up": "Request another recommendation with updated observations if needed.",
        }
        if selected_warnings:
            monitoring["warning_signs"] = selected_warnings
        safety: dict[str, object] = {"warnings": selected_warnings}
        weather_advice = list(selected_weather)
        if (
            isinstance(weather.get("warning"), str)
            and (warning := _safe_text(weather["warning"]))
            and warning not in weather_advice
        ):
            weather_advice.append(warning)
        if weather_advice:
            safety["weather"] = weather_advice
        if recommendation.contact_recommendation:
            contact = recommendation.contact_recommendation
            if contact.specialist_required:
                safety["professional_assistance"] = {
                    "category": contact.specialist_category or "agricultural_specialist",
                    "reason": contact.specialist_reason or "Field assessment advised.",
                }
        references: dict[str, object] = {
            "recommendation_id": recommendation.recommendation_id,
            "recommendation_date": recommendation.created_at.isoformat(),
            "document_date": generated_at.isoformat(),
            "sources": rule_sources,
        }
        if not rule_sources:
            references["source_note"] = "No explicit technical references were attached."
        if validation_status != "validated":
            references["limitations"] = "Preliminary guidance; agronomic validation is required."

        sections = [
            {"id": key, "fields": value}
            for key, value in (
                ("cover", cover),
                ("executive_summary", executive_summary),
                ("farm_context", farm_context),
                ("diagnosis", diagnosis),
                ("recommendations", recommendations),
                ("action_calendar", action_calendar),
                ("monitoring", monitoring),
                ("safety", safety),
                ("references", references),
            )
        ]
        general_information: dict[str, object] = {
            "title": recommendation.primary.name,
            "crop": recommendation.crop_id,
            "subject": subject,
        }
        for key in ("region", "locality", "surface_area", "variety", "stage"):
            if key in farm_context:
                general_information[key] = farm_context[key]

        content: dict[str, object] = {
            "sections": sections,
            "language": language_info,
            "cover": cover,
            "executive_summary": executive_summary,
            "farm_context": farm_context,
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "action_calendar": action_calendar,
            "monitoring": monitoring,
            "safety": safety,
            "references": references,
            "general_information": general_information,
        }
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

    def list_visible(
        self, *, owner_id: str, crop_id: str | None = None, subject: str | None = None
    ) -> list[TechnicalFiche]:
        return [
            fiche
            for fiche in self._all()
            if (fiche.status == "PUBLISHED" or fiche.owner_id == owner_id)
            and (not crop_id or fiche.crop_id == crop_id)
            and (not subject or fiche.subject == subject)
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
