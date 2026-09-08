"""Weather adapters used for development and tests."""

from __future__ import annotations

from typing import Any

from engine.exceptions import ProviderUnavailableError


class UnavailableWeatherProvider:
    """Safe default until a real weather adapter is configured."""

    def __init__(self, reason: str = "no weather adapter is configured") -> None:
        self._reason = reason

    def get_current(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None:
        raise ProviderUnavailableError(self._reason)

    def get_forecast(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None:
        raise ProviderUnavailableError(self._reason)


class StaticWeatherProvider:
    """Deterministic adapter for scenarios and local demonstrations."""

    def __init__(
        self,
        current: dict[str, Any] | None = None,
        forecast: dict[str, Any] | None = None,
    ) -> None:
        self._current = dict(current) if current else None
        self._forecast = dict(forecast) if forecast else None

    def get_current(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None:
        return dict(self._current) if self._current else None

    def get_forecast(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any] | None:
        return dict(self._forecast) if self._forecast else None

