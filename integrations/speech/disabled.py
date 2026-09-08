"""Explicitly disabled TTS adapter for the V1 development baseline."""

from engine.exceptions import ProviderUnavailableError


class DisabledSpeechProvider:
    def synthesize(self, text: str, language: str) -> bytes:
        raise ProviderUnavailableError("no text-to-speech adapter is configured")

