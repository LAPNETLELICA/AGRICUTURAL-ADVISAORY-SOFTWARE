from pathlib import Path

import pytest

from engine.config import Settings


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("KNOWLEDGE_PATH", "knowledge/custom-release")
    monkeypatch.setenv("SMS_MAX_LENGTH", "320")
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example, https://two.example")
    settings = Settings.from_env()
    assert settings.environment == "production"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.knowledge_path == Path("knowledge/custom-release")
    assert settings.sms_max_length == 320
    assert settings.allowed_knowledge_statuses == frozenset({"validated"})
    assert settings.cors_origins == ("https://one.example", "https://two.example")


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
