"""Fish Audio text-to-speech provider."""

from __future__ import annotations

import requests

from engine.exceptions import ProviderUnavailableError


class FishAudioSpeechProvider:
    _URL = "https://api.fish.audio/v1/tts"

    def __init__(self, api_key: str, *, timeout_seconds: float = 20.0) -> None:
        if not api_key or api_key.startswith("your_actual_"):
            raise ProviderUnavailableError("FISH_AUDIO_API_KEY is not configured")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def synthesize(self, text: str, language: str) -> bytes:
        del language
        try:
            response = requests.post(
                self._URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "model": "s2.1-pro-free",
                },
                json={"text": text, "format": "mp3"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise ProviderUnavailableError(f"Fish Audio unavailable: {exc}") from exc
