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

        return cls(
            environment=environment,
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=port,
            log_level=os.getenv("APP_LOG_LEVEL", "INFO").upper(),
            knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", "knowledge")),
            sms_max_length=sms_max_length,
            cors_origins=_csv(
                os.getenv(
                    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
                )
            ),
        )
