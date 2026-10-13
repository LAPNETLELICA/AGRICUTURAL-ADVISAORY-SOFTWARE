from pathlib import Path

import pytest

from engine.bootstrap import build_container
from engine.config import Settings
from integrations.speech import DisabledSpeechProvider, DisabledTranscriptionProvider


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("KNOWLEDGE_PATH", "BASE_CONNAISSANCES_AGRICOLES/custom-release")
    monkeypatch.setenv("SMS_MAX_LENGTH", "320")
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example, https://two.example")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("FISH_AUDIO_API_KEY", "fish-test")
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "weather-test")
    monkeypatch.setenv("WEATHER_PROVIDER", "openweathermap")
    monkeypatch.setenv("SPEECH_PROVIDER", "fish_audio")
    monkeypatch.setenv("TRANSCRIPTION_PROVIDER", "groq")
    settings = Settings.from_env()
    assert settings.environment == "production"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.knowledge_path == Path("BASE_CONNAISSANCES_AGRICOLES/custom-release")
    assert settings.sms_max_length == 320
    assert settings.allowed_knowledge_statuses == frozenset({"validated"})
    assert settings.cors_origins == ("https://one.example", "https://two.example")
    assert settings.groq_api_key == "gsk-test"
    assert settings.fish_audio_api_key == "fish-test"
    assert settings.openweathermap_api_key == "weather-test"
    assert settings.weather_provider == "openweathermap"
    assert settings.transcription_provider == "groq"


def test_settings_loads_provider_keys_from_project_dotenv(monkeypatch, tmp_path):
    """A local .env file must work without exporting values in the shell."""
    (tmp_path / ".env").write_text(
        "GROQ_API_KEY=gsk-from-dotenv\n"
        "FISH_AUDIO_API_KEY=fish-from-dotenv\n"
        "OPENWEATHERMAP_API_KEY=weather-from-dotenv\n"
        "WEATHER_PROVIDER=openweathermap\n"
        "SPEECH_PROVIDER=fish_audio\n"
        "TRANSCRIPTION_PROVIDER=groq\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    for variable in (
        "GROQ_API_KEY",
        "FISH_AUDIO_API_KEY",
        "OPENWEATHERMAP_API_KEY",
        "WEATHER_PROVIDER",
        "SPEECH_PROVIDER",
        "TRANSCRIPTION_PROVIDER",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings.from_env()

    assert settings.groq_api_key == "gsk-from-dotenv"
    assert settings.fish_audio_api_key == "fish-from-dotenv"
    assert settings.openweathermap_api_key == "weather-from-dotenv"
    assert settings.weather_provider == "openweathermap"
    assert settings.speech_provider == "fish_audio"
    assert settings.transcription_provider == "groq"


def test_placeholder_provider_keys_keep_safe_fallbacks():
    settings = Settings(
        knowledge_path=Path(__file__).resolve().parents[1] / "BASE_CONNAISSANCES_AGRICOLES",
        weather_provider="openweathermap",
        openweathermap_api_key="your_actual_openweathermap_key_here",
        speech_provider="fish_audio",
        fish_audio_api_key="your_actual_fish_audio_key_here",
        transcription_provider="groq",
        groq_api_key="gsk_your_actual_groq_key_here",
    )

    container = build_container(settings)

    assert isinstance(container.speech, DisabledSpeechProvider)
    assert isinstance(container.transcription, DisabledTranscriptionProvider)


def test_settings_reads_tranzak_and_proactive_options(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "tranzak")
    monkeypatch.setenv("TRANZAK_APP_ID", "test-app")
    monkeypatch.setenv("PROACTIVE_SMS_INTERVAL_SECONDS", "3600")

    settings = Settings.from_env()

    assert settings.sms_provider == "tranzak"
    assert settings.tranzak_app_id == "test-app"
    assert settings.proactive_sms_interval_seconds == 3600


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("APP_ENV", "staging", "APP_ENV"),
        ("APP_PORT", "70000", "APP_PORT"),
        ("SMS_MAX_LENGTH", "20", "SMS_MAX_LENGTH"),
    ],
)
def test_invalid_settings_fail(monkeypatch, name, value, message):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=message):
        Settings.from_env()
