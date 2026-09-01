"""Crop-first Past + Present + Future context assembly."""

from __future__ import annotations

from typing import Any

from engine.exceptions import CropNotFoundError, ProviderUnavailableError
from engine.interfaces.providers import (
    CropPassportRepository,
    CropProvider,
    HistoryProvider,
    WeatherProvider,
)
from engine.models.domain import AgriculturalContext, CropProfile
from engine.models.requests import AdvisoryRequest


class CropContextBuilder:
    def __init__(
        self,
        *,
        crop_provider: CropProvider,
        history_provider: HistoryProvider,
        weather_provider: WeatherProvider,
        passport_repository: CropPassportRepository,
    ) -> None:
        self._crop_provider = crop_provider
        self._history_provider = history_provider
        self._weather_provider = weather_provider
        self._passport_repository = passport_repository

    def build(self, request: AdvisoryRequest) -> AgriculturalContext:
        profile = self._profile(request)
        crop_family = profile.family if profile else None
        provider_history = self._history_provider.get_relevant_history(
            request.farmer_id, request.crop_id, crop_family
        )
        request_history = self._filter_history(request.history, request.crop_id, crop_family)
        history = self._deduplicate_history([*provider_history, *request_history])

        uncertainty: list[str] = []
        current_weather, forecast_weather = self._weather(request, uncertainty)
        present_weather = dict(current_weather or {})
        present_weather.update(request.evidence.weather)
        future = dict(request.evidence.future)
        supplied_forecast = future.get("weather")
        if isinstance(supplied_forecast, dict):
            merged_forecast = dict(forecast_weather or {})
            merged_forecast.update(supplied_forecast)
            future["weather"] = merged_forecast
        elif forecast_weather:
            future["weather"] = forecast_weather

        if request.cultivation_period:
            future["cultivation_period"] = request.cultivation_period

        passport_context: dict[str, Any] | None = None
        if request.passport_id:
            passport = self._passport_repository.get(request.passport_id)
            if passport:
                passport_context = passport.model_dump(mode="json")

        return AgriculturalContext(
            request_id=request.request_id,
            crop_id=request.crop_id,
            crop_description=request.crop_description,
            channel=request.channel,
            farmer_id=request.farmer_id,
            passport_id=request.passport_id,
            crop_profile=profile,
            region=request.region,
            locality=request.locality,
            past={
                "history": history,
                "passport": passport_context,
            },
            present={
                "question": request.question,
                "objective": request.objective,
                "current_stage": request.current_stage,
                "soil": request.evidence.soil,
                "topography": request.evidence.topography,
                "weather": present_weather,
                "observations": request.evidence.observations,
                "practices": request.evidence.practices,
                "image_references": request.evidence.image_references,
                "cultivation_period": request.cultivation_period,
            },
            future=future,
            uncertainty=uncertainty,
        )

    def _profile(self, request: AdvisoryRequest) -> CropProfile | None:
        if request.crop_discovery:
            return None
        profile = self._crop_provider.get_crop_profile(request.crop_id)
        if profile is None:
            raise CropNotFoundError(f"crop profile not found: {request.crop_id}")
        return profile

    def _weather(
        self,
        request: AdvisoryRequest,
        uncertainty: list[str],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        current: dict[str, Any] | None = None
        forecast: dict[str, Any] | None = None
        try:
            current = self._weather_provider.get_current(
                request.region, request.locality, request.crop_id
            )
            forecast = self._weather_provider.get_forecast(
                request.region, request.locality, request.crop_id
            )
            if current is None:
                uncertainty.append("Current weather data is unavailable.")
            if forecast is None:
                uncertainty.append("Forecast weather data is unavailable.")
        except (ProviderUnavailableError, TimeoutError, ConnectionError) as exc:
            uncertainty.append(f"Weather provider unavailable: {exc}")
        return current, forecast

    @staticmethod
    def _filter_history(
        history: list[dict[str, Any]], crop_id: str, crop_family: str | None
    ) -> list[dict[str, Any]]:
        relevant: list[dict[str, Any]] = []
        for event in history:
            event_crop = event.get("crop_id")
            event_family = event.get("crop_family")
            if event_crop == crop_id or (crop_family and event_family == crop_family):
                relevant.append(event)
        return relevant

    @staticmethod
    def _deduplicate_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for event in history:
            key = repr(sorted(event.items()))
            if key not in seen:
                seen.add(key)
                result.append(event)
        return result

