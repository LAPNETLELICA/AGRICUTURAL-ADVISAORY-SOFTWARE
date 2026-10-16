from __future__ import annotations

import asyncio
import base64
import importlib.util
import traceback
from types import SimpleNamespace
from typing import Any

import pytest
import requests

from api.transcription import transcribe_voice
from api.voice import voice_advisory
from engine.exceptions import ProviderUnavailableError
from engine.models.requests import MobileAdvisoryRequest
from integrations.speech.fish_audio import FishAudioSpeechProvider
from integrations.speech.groq import GroqTranscriptionProvider


class _Response:
    def __init__(self, payload: dict[str, Any] | None = None, content: bytes = b"") -> None:
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_openweathermap_uses_cameroon_location_and_maps_conditions(monkeypatch):
    assert importlib.util.find_spec("integrations.weather.openweathermap") is not None
    from integrations.weather.openweathermap import OpenWeatherMapProvider

    sent: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> _Response:
        sent["url"] = url
        sent.update(kwargs)
        return _Response(
            {
                "main": {"temp": 22.0, "humidity": 88},
                "rain": {"1h": 4.2},
                "weather": [{"description": "light rain"}],
                "list": [
                    {
                        "main": {"temp_min": 16.0, "temp_max": 24.0},
                        "rain": {"3h": 8.5},
                        "weather": [{"description": "moderate rain"}],
                    }
                ],
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)
    provider = OpenWeatherMapProvider("weather-test")

    current = provider.get_current("West", "Bafoussam", "irish-potato")
    forecast = provider.get_forecast("West", "Bafoussam", "irish-potato")

    assert sent["url"] == "https://api.openweathermap.org/data/2.5/forecast"
    assert sent["params"]["q"] == "Bafoussam, West, Cameroon"
    assert sent["params"]["appid"] == "weather-test"
    assert sent["params"]["units"] == "metric"
    assert current == {
        "temperature_c": 22.0,
        "rainfall_mm": 4.2,
        "humidity": 88,
        "condition": "light rain",
    }
    assert forecast["rainfall_mm"] == 8.5
    assert forecast["condition"] == "moderate rain"


def test_openweathermap_failure_does_not_expose_api_key_in_traceback(monkeypatch):
    from integrations.weather.openweathermap import OpenWeatherMapProvider

    key = "secret-test-weather-key"

    def failed_get(*args, **kwargs):
        raise requests.ConnectionError(f"request failed: appid={key}")

    monkeypatch.setattr(requests, "get", failed_get)
    with pytest.raises(ProviderUnavailableError) as failure:
        OpenWeatherMapProvider(key).get_current("West", "Bafoussam", "tomato")
    assert key not in "".join(traceback.format_exception(failure.value))


def test_fish_audio_returns_mp3_bytes(monkeypatch):
    sent: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> _Response:
        sent["url"] = url
        sent.update(kwargs)
        return _Response(content=b"fake-mp3")

    monkeypatch.setattr(requests, "post", fake_post)

    audio = FishAudioSpeechProvider("fish-test").synthesize("Water in the morning.", "en")

    assert audio == b"fake-mp3"
    assert sent["headers"]["Authorization"] == "Bearer fish-test"
    assert sent["json"] == {"text": "Water in the morning.", "format": "mp3"}


def test_groq_transcribes_an_audio_upload(monkeypatch):
    sent: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> _Response:
        sent["url"] = url
        sent.update(kwargs)
        return _Response({"text": "My potato leaves have spots."})

    monkeypatch.setattr(requests, "post", fake_post)

    text = GroqTranscriptionProvider("gsk-test").transcribe(
        b"audio-bytes", filename="question.webm", mime_type="audio/webm", language="en"
    )

    assert text == "My potato leaves have spots."
    assert sent["url"] == "https://api.groq.com/openai/v1/audio/transcriptions"
    assert sent["headers"]["Authorization"] == "Bearer gsk-test"
    assert sent["data"]["model"] == "whisper-large-v3-turbo"
    assert sent["data"]["language"] == "en"
    assert sent["files"]["file"] == ("question.webm", b"audio-bytes", "audio/webm")


@pytest.mark.parametrize(
    ("module", "provider_name", "key"),
    [
        (
            "integrations.weather.openweathermap",
            "OpenWeatherMapProvider",
            "your_actual_openweathermap_key_here",
        ),
        (
            "integrations.speech.fish_audio",
            "FishAudioSpeechProvider",
            "your_actual_fish_audio_key_here",
        ),
        ("integrations.speech.groq", "GroqTranscriptionProvider", "gsk_your_actual_groq_key_here"),
    ],
)
def test_provider_rejects_placeholder_key(module: str, provider_name: str, key: str):
    assert importlib.util.find_spec(module) is not None
    provider = getattr(__import__(module, fromlist=[provider_name]), provider_name)
    with pytest.raises(ProviderUnavailableError):
        provider(key)


def test_transcription_endpoint_returns_provider_text():
    class StubTranscription:
        def transcribe(self, content: bytes, **kwargs: Any) -> str:
            assert content == b"audio-bytes"
            assert kwargs["filename"] == "question.webm"
            return "My potato leaves have spots."

    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(container=SimpleNamespace(transcription=StubTranscription()))
        )
    )

    class AudioUpload:
        content_type = "audio/webm"
        filename = "question.webm"

        async def read(self) -> bytes:
            return b"audio-bytes"

    response = asyncio.run(
        transcribe_voice(
            request=request,
            principal=SimpleNamespace(),
            file=AudioUpload(),
            language="en",
        )
    )

    assert response.text == "My potato leaves have spots."
    assert response.language == "en"


def test_voice_endpoint_speaks_a_generated_cameroon_recommendation(container):
    class StubSpeech:
        def synthesize(self, text: str, language: str) -> bytes:
            assert "Action:" in text
            assert language == "en"
            return b"recommendation-mp3"

    class MediaService:
        def validate_references(self, farmer_id: str, references: list[str]) -> None:
            assert farmer_id == "voice-farmer"
            assert references == []

    container.speech = StubSpeech()
    http_request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(media_service=MediaService()))
    )
    request = MobileAdvisoryRequest(
        farmer_id="voice-farmer",
        crop_id="irish-potato",
        question="How can I prepare this plot?",
        objective="yield_improvement",
        region="West",
        locality="Bafoussam",
        current_stage="pre-planting",
    )
    principal = SimpleNamespace(subject="voice-farmer", is_admin=False)

    response = voice_advisory(request, http_request, container, principal)

    assert response.audio_available is True
    assert response.audio_media_type == "audio/mpeg"
    assert base64.b64decode(response.audio_base64 or "") == b"recommendation-mp3"
    assert "Action:" in response.text
