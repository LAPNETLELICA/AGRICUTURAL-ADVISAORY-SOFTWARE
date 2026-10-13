"""Explicitly disabled TTS adapter for the V1 development baseline."""

from engine.exceptions import ProviderUnavailableError


class DisabledSpeechProvider:
    def synthesize(self, text: str, language: str) -> bytes:
        raise ProviderUnavailableError("no text-to-speech adapter is configured")


class DisabledTranscriptionProvider:
    def transcribe(
        self,
        content: bytes,
        *,
        filename: str,
        mime_type: str,
        language: str | None = None,
    ) -> str:
        raise ProviderUnavailableError("no speech-to-text adapter is configured")
