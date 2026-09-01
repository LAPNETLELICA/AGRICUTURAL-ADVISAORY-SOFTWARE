"""Thread-safe in-memory V1 stores, replaceable behind repository interfaces."""

from __future__ import annotations

from threading import RLock

from engine.models.domain import CropPassport
from engine.models.responses import Recommendation, TraceRecord


class InMemoryTraceRecorder:
    def __init__(self) -> None:
        self._items: dict[str, TraceRecord] = {}
        self._lock = RLock()

    def record(self, trace: TraceRecord) -> None:
        with self._lock:
            self._items[trace.trace_id] = trace.model_copy(deep=True)

    def get(self, trace_id: str) -> TraceRecord | None:
        with self._lock:
            item = self._items.get(trace_id)
            return item.model_copy(deep=True) if item else None


class InMemoryRecommendationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Recommendation] = {}
        self._lock = RLock()

    def save(self, recommendation: Recommendation) -> None:
        with self._lock:
            self._items[recommendation.recommendation_id] = recommendation.model_copy(deep=True)

    def get(self, recommendation_id: str) -> Recommendation | None:
        with self._lock:
            item = self._items.get(recommendation_id)
            return item.model_copy(deep=True) if item else None


class InMemoryCropPassportRepository:
    def __init__(self) -> None:
        self._items: dict[str, CropPassport] = {}
        self._lock = RLock()

    def get(self, passport_id: str) -> CropPassport | None:
        with self._lock:
            item = self._items.get(passport_id)
            return item.model_copy(deep=True) if item else None

    def find(self, farmer_id: str, crop_id: str, plot_ref: str) -> CropPassport | None:
        with self._lock:
            for item in self._items.values():
                if (
                    item.farmer_id == farmer_id
                    and item.crop_id == crop_id
                    and item.plot_ref == plot_ref
                ):
                    return item.model_copy(deep=True)
        return None

    def save(self, passport: CropPassport) -> None:
        with self._lock:
            self._items[passport.passport_id] = passport.model_copy(deep=True)

