"""Groq speech-to-text provider for farmer voice questions."""

from __future__ import annotations

from typing import Any

import requests

from engine.exceptions import ProviderUnavailableError


class GroqTranscriptionProvider:
    """Transcribe an uploaded voice recording through Groq's OpenAI-compatible API."""

    _URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    _MODEL = "whisper-large-v3-turbo"

    def __init__(self, api_key: str, *, timeout_seconds: float = 25.0) -> None:
        if (
            not api_key
            or api_key.startswith("your_actual_")
            or api_key.startswith("gsk_your_actual")
        ):
            raise ProviderUnavailableError("GROQ_API_KEY is not configured")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def transcribe(
        self,
        content: bytes,
        *,
        filename: str,
        mime_type: str,
        language: str | None = None,
    ) -> str:
        data: dict[str, str] = {"model": self._MODEL}
        if language:
            data["language"] = language
        try:
            response = requests.post(
                self._URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                data=data,
                files={"file": (filename, content, mime_type)},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderUnavailableError(f"Groq transcription unavailable: {exc}") from exc

        payload: dict[str, Any] = response.json()
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ProviderUnavailableError("Groq returned no transcribed text")
        return text.strip()
