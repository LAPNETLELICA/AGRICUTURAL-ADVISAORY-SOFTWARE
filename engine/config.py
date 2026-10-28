"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with production-safe knowledge defaults."""

    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    knowledge_path: Path = Path("BASE_CONNAISSANCES_AGRICOLES")
    sms_max_length: int = 160
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
        "https://lapnetlelica.github.io",
    )
    database_url: str | None = None
    auth_required: bool = False
    auth_secret: str = "development-auth-secret-change-me"
    auth_store_path: Path = Path("runtime/users.json")
    auth_token_ttl_seconds: int = 3600
    admin_username: str = "admin"
    admin_password: str | None = None
    google_client_id: str | None = None
    weather_provider: str = "disabled"
    translation_provider: str = "passthrough"
    speech_provider: str = "disabled"
    transcription_provider: str = "disabled"
    sms_provider: str = "simulator"
    tranzak_app_id: str | None = None
    tranzak_app_key: str | None = None
    tranzak_sender_id: str | None = None
    tranzak_base_url: str = "https://sandbox.dsapi.tranzak.me"
    tranzak_timeout_seconds: float = 10.0
    proactive_sms_enabled: bool = False
    proactive_sms_interval_seconds: int = 3600
    groq_api_key: str | None = None
    fish_audio_api_key: str | None = None
    openweathermap_api_key: str | None = None
    media_storage_path: Path = Path("runtime/media")
    media_max_bytes: int = 10 * 1024 * 1024
    media_retention_days: int = 180
    trace_retention_days: int = 180
    history_retention_days: int = 730
    sms_retention_days: int = 90
    audit_retention_days: int = 365

    @property
    def allowed_knowledge_statuses(self) -> frozenset[str]:
        if self.environment.lower() == "production":
            return frozenset({"validated"})
        return frozenset({"validated", "draft", "test_only"})

    @classmethod
    def from_env(cls) -> Settings:
        # Load the .env alongside the command being run. Shell-exported values
        # remain authoritative, which keeps deployment configuration intact.
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
        environment = os.getenv("APP_ENV", "development").strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production")

        port = int(os.getenv("APP_PORT", "8000"))
        sms_max_length = int(os.getenv("SMS_MAX_LENGTH", "160"))
        if not 1 <= port <= 65535:
            raise ValueError("APP_PORT must be between 1 and 65535")
        if not 70 <= sms_max_length <= 918:
            raise ValueError("SMS_MAX_LENGTH must be between 70 and 918")

        sms_provider = os.getenv("SMS_PROVIDER", "simulator").strip().lower()
        if sms_provider not in {"simulator", "tranzak"}:
            raise ValueError("SMS_PROVIDER must be simulator or tranzak")
        tranzak_timeout_seconds = float(os.getenv("TRANZAK_TIMEOUT_SECONDS", "10"))
        if tranzak_timeout_seconds <= 0:
            raise ValueError("TRANZAK_TIMEOUT_SECONDS must be greater than zero")
        proactive_sms_interval_seconds = int(os.getenv("PROACTIVE_SMS_INTERVAL_SECONDS", "3600"))
        if proactive_sms_interval_seconds < 60:
            raise ValueError("PROACTIVE_SMS_INTERVAL_SECONDS must be at least 60")

        auth_required = os.getenv(
            "AUTH_REQUIRED", "true" if environment == "production" else "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        auth_secret = os.getenv("AUTH_SECRET", "development-auth-secret-change-me")
        admin_password = os.getenv("ADMIN_PASSWORD") or None
        media_max_bytes = int(os.getenv("MEDIA_MAX_BYTES", str(10 * 1024 * 1024)))
        if not 1024 <= media_max_bytes <= 50 * 1024 * 1024:
            raise ValueError("MEDIA_MAX_BYTES must be between 1 KiB and 50 MiB")

        def retention_days(name: str, default: int) -> int:
            value = int(os.getenv(name, str(default)))
            if value < 1:
                raise ValueError(f"{name} must be at least 1 day")
            return value

        return cls(
            environment=environment,
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=port,
            log_level=os.getenv("APP_LOG_LEVEL", "INFO").upper(),
            knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", "BASE_CONNAISSANCES_AGRICOLES")),
            sms_max_length=sms_max_length,
            cors_origins=_csv(
                os.getenv(
                    "CORS_ORIGINS",
                    "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000,http://localhost:8080,http://localhost:8000,http://127.0.0.1:8000,http://0.0.0.0:8000,https://lapnetlelica.github.io",
                )
            ),
            database_url=os.getenv("DATABASE_URL") or None,
            auth_required=auth_required,
            auth_secret=auth_secret,
            auth_store_path=Path(os.getenv("AUTH_STORE_PATH", "runtime/users.json")),
            auth_token_ttl_seconds=int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "3600")),
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password=admin_password,
            google_client_id=os.getenv("GOOGLE_CLIENT_ID") or None,
            weather_provider=os.getenv("WEATHER_PROVIDER", "disabled"),
            translation_provider=os.getenv("TRANSLATION_PROVIDER", "passthrough"),
            speech_provider=os.getenv("SPEECH_PROVIDER", "disabled"),
            transcription_provider=os.getenv("TRANSCRIPTION_PROVIDER", "disabled"),
            sms_provider=sms_provider,
            tranzak_app_id=os.getenv("TRANZAK_APP_ID") or None,
            tranzak_app_key=os.getenv("TRANZAK_APP_KEY") or None,
            tranzak_sender_id=os.getenv("TRANZAK_SENDER_ID") or None,
            tranzak_base_url=os.getenv(
                "TRANZAK_BASE_URL", "https://sandbox.dsapi.tranzak.me"
            ).rstrip("/"),
            tranzak_timeout_seconds=tranzak_timeout_seconds,
            proactive_sms_enabled=os.getenv("PROACTIVE_SMS_ENABLED", "false").strip().lower()
            in {"1", "true", "yes", "on"},
            proactive_sms_interval_seconds=proactive_sms_interval_seconds,
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            fish_audio_api_key=os.getenv("FISH_AUDIO_API_KEY") or None,
            openweathermap_api_key=os.getenv("OPENWEATHERMAP_API_KEY") or None,
            media_storage_path=Path(os.getenv("MEDIA_STORAGE_PATH", "runtime/media")),
            media_max_bytes=media_max_bytes,
            media_retention_days=retention_days("MEDIA_RETENTION_DAYS", 180),
            trace_retention_days=retention_days("TRACE_RETENTION_DAYS", 180),
            history_retention_days=retention_days("HISTORY_RETENTION_DAYS", 730),
            sms_retention_days=retention_days("SMS_RETENTION_DAYS", 90),
            audit_retention_days=retention_days("AUDIT_RETENTION_DAYS", 365),
        )
