"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with production-safe knowledge defaults."""

    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    knowledge_path: Path = Path("knowledge")
    sms_max_length: int = 160
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:8080")
    database_url: str | None = None
    auth_required: bool = False
    auth_secret: str = "development-auth-secret-change-me"
    auth_store_path: Path = Path("runtime/users.json")
    auth_token_ttl_seconds: int = 3600
    admin_username: str = "admin"
    admin_password: str | None = None
    weather_provider: str = "disabled"
    translation_provider: str = "passthrough"
    speech_provider: str = "disabled"
    sms_provider: str = "simulator"
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
        environment = os.getenv("APP_ENV", "development").strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production")

        port = int(os.getenv("APP_PORT", "8000"))
        sms_max_length = int(os.getenv("SMS_MAX_LENGTH", "160"))
        if not 1 <= port <= 65535:
            raise ValueError("APP_PORT must be between 1 and 65535")
        if not 70 <= sms_max_length <= 918:
            raise ValueError("SMS_MAX_LENGTH must be between 70 and 918")

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
            knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", "knowledge")),
            sms_max_length=sms_max_length,
            cors_origins=_csv(
                os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
            ),
            database_url=os.getenv("DATABASE_URL") or None,
            auth_required=auth_required,
            auth_secret=auth_secret,
            auth_store_path=Path(os.getenv("AUTH_STORE_PATH", "runtime/users.json")),
            auth_token_ttl_seconds=int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "3600")),
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password=admin_password,
            weather_provider=os.getenv("WEATHER_PROVIDER", "disabled"),
            translation_provider=os.getenv("TRANSLATION_PROVIDER", "passthrough"),
            speech_provider=os.getenv("SPEECH_PROVIDER", "disabled"),
            sms_provider=os.getenv("SMS_PROVIDER", "simulator"),
            media_storage_path=Path(os.getenv("MEDIA_STORAGE_PATH", "runtime/media")),
            media_max_bytes=media_max_bytes,
            media_retention_days=retention_days("MEDIA_RETENTION_DAYS", 180),
            trace_retention_days=retention_days("TRACE_RETENTION_DAYS", 180),
            history_retention_days=retention_days("HISTORY_RETENTION_DAYS", 730),
            sms_retention_days=retention_days("SMS_RETENTION_DAYS", 90),
            audit_retention_days=retention_days("AUDIT_RETENTION_DAYS", 365),
        )
