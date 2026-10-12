"""WeatherAPI.com adapter constrained to Cameroon location queries."""

from __future__ import annotations

from typing import Any

import requests

from engine.exceptions import ProviderUnavailableError


class WeatherAPIProvider:
    """Read current conditions and short forecast for a Cameroon locality."""

    _URL = "https://api.weatherapi.com/v1/forecast.json"

    def __init__(self, api_key: str, *, timeout_seconds: float = 8.0) -> None:
        if not api_key or api_key.startswith("your_actual_"):
            raise ProviderUnavailableError("WEATHERAPI_KEY is not configured")
        self._api_key = api_key
        self._timeout = timeout_seconds

    @staticmethod
    def _query(region: str | None, locality: str | None) -> str:
        parts = [part.strip() for part in (locality, region, "Cameroon") if part and part.strip()]
        return ", ".join(parts)

    def _payload(self, region: str | None, locality: str | None) -> dict[str, Any]:
        try:
            response = requests.get(
                self._URL,
                params={
                    "key": self._api_key,
                    "q": self._query(region, locality),
                    "days": 2,
                    "aqi": "no",
                    "alerts": "no",
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise ProviderUnavailableError(f"WeatherAPI unavailable: {exc}") from exc

    def get_current(self, region: str | None, locality: str | None, crop_id: str) -> dict[str, Any]:
        del crop_id
        current = self._payload(region, locality).get("current", {})
        return {
            "temperature_c": current.get("temp_c"),
            "rainfall_mm": current.get("precip_mm"),
            "humidity": current.get("humidity"),
            "condition": current.get("condition", {}).get("text"),
        }

    def get_forecast(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any]:
        del crop_id
        days = self._payload(region, locality).get("forecast", {}).get("forecastday", [])
        day = days[1]["day"] if len(days) > 1 else (days[0]["day"] if days else {})
        return {
            "rainfall_mm": day.get("totalprecip_mm"),
            "temperature_min_c": day.get("mintemp_c"),
            "temperature_max_c": day.get("maxtemp_c"),
            "condition": day.get("condition", {}).get("text"),
        }
