"""OpenWeatherMap adapter constrained to Cameroon location queries."""

from __future__ import annotations

from typing import Any

import requests

from engine.exceptions import ProviderUnavailableError


class OpenWeatherMapProvider:
    """Read current conditions and short forecast for a Cameroon locality."""

    _CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
    _FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str, *, timeout_seconds: float = 8.0) -> None:
        if not api_key or api_key.startswith("your_actual_"):
            raise ProviderUnavailableError("OPENWEATHERMAP_API_KEY is not configured")
        self._api_key = api_key
        self._timeout = timeout_seconds

    @staticmethod
    def _query(region: str | None, locality: str | None) -> str:
        parts = [part.strip() for part in (locality, region, "Cameroon") if part and part.strip()]
        return ", ".join(parts)

    def _payload(self, url: str, region: str | None, locality: str | None) -> dict[str, Any]:
        try:
            response = requests.get(
                url,
                params={
                    "appid": self._api_key,
                    "q": self._query(region, locality),
                    "units": "metric",
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            raise ProviderUnavailableError("OpenWeatherMap is unavailable") from None
        if not isinstance(payload, dict):
            raise ProviderUnavailableError("OpenWeatherMap returned an invalid response")
        return payload

    @staticmethod
    def _condition(payload: dict[str, Any]) -> str | None:
        weather = payload.get("weather")
        if not isinstance(weather, list) or not weather or not isinstance(weather[0], dict):
            return None
        description = weather[0].get("description")
        return description if isinstance(description, str) else None

    @staticmethod
    def _rainfall(payload: dict[str, Any]) -> float | None:
        rain = payload.get("rain")
        if not isinstance(rain, dict):
            return None
        value = rain.get("1h", rain.get("3h"))
        return value if isinstance(value, (int, float)) else None

    def get_current(self, region: str | None, locality: str | None, crop_id: str) -> dict[str, Any]:
        del crop_id
        payload = self._payload(self._CURRENT_URL, region, locality)
        raw_current = payload.get("main")
        current = raw_current if isinstance(raw_current, dict) else {}
        return {
            "temperature_c": current.get("temp"),
            "rainfall_mm": self._rainfall(payload),
            "humidity": current.get("humidity"),
            "condition": self._condition(payload),
        }

    def get_forecast(
        self, region: str | None, locality: str | None, crop_id: str
    ) -> dict[str, Any]:
        del crop_id
        payload = self._payload(self._FORECAST_URL, region, locality)
        entries = payload.get("list")
        day = (
            entries[0]
            if isinstance(entries, list) and entries and isinstance(entries[0], dict)
            else {}
        )
        raw_temperatures = day.get("main")
        temperatures = raw_temperatures if isinstance(raw_temperatures, dict) else {}
        return {
            "rainfall_mm": self._rainfall(day),
            "temperature_min_c": temperatures.get("temp_min"),
            "temperature_max_c": temperatures.get("temp_max"),
            "condition": self._condition(day),
        }
