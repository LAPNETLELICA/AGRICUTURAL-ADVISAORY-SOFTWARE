"""Replaceable provider and repository contracts.

All external systems and Developer 2 knowledge enter through these protocols.
"""

from __future__ import annotations

from typing import Any, Protocol

from engine.models.domain import (
    AgriculturalContext,
    CropPassport,
    CropProfile,
    Rule,
)
from engine.models.enums import TreeId
from engine.models.responses import DeliveryReceipt, Recommendation, TraceRecord


class CropProvider(Protocol):
    def get_crop_profile(self, crop_id: str) -> CropProfile | None: ...

    def list_crop_profiles(self) -> list[CropProfile]: ...


class KnowledgeProvider(Protocol):
    def get_relevant_rules(
        self,
        crop_id: str,
        context: AgriculturalContext,
        trees: list[TreeId],
    ) -> list[Rule]: ...

    def metadata(self) -> dict[str, Any]: ...


class WeatherProvider(Protocol):
    def get_current(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None: ...

    def get_forecast(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None: ...


class HistoryProvider(Protocol):
    def get_relevant_history(
        self,
        farmer_id: str | None,
        crop_id: str,
        crop_family: str | None,
    ) -> list[dict[str, Any]]: ...

    def append(self, farmer_id: str | None, event: dict[str, Any]) -> None: ...


class TranslationProvider(Protocol):
    def translate(self, text: str, target_language: str) -> str: ...


class SpeechProvider(Protocol):
    def synthesize(self, text: str, language: str) -> bytes: ...


class SMSProvider(Protocol):
    def send(
        self,
        recipient_id: str,
        crop_id: str,
        message: str,
        recommendation_id: str | None = None,
    ) -> DeliveryReceipt: ...

    def inbox(self, recipient_id: str) -> list[DeliveryReceipt]: ...


class TraceRecorder(Protocol):
    def record(self, trace: TraceRecord) -> None: ...

    def get(self, trace_id: str) -> TraceRecord | None: ...


class RecommendationRepository(Protocol):
    def save(self, recommendation: Recommendation) -> None: ...

    def get(self, recommendation_id: str) -> Recommendation | None: ...


class CropPassportRepository(Protocol):
    def get(self, passport_id: str) -> CropPassport | None: ...

    def find(self, farmer_id: str, crop_id: str, plot_ref: str) -> CropPassport | None: ...

    def save(self, passport: CropPassport) -> None: ...

