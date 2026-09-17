"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import (
    admin,
    auth,
    dashboard,
    education,
    media,
    mobile,
    notifications,
    privacy,
    sms,
    system,
    voice,
)
from engine import __version__
from engine.bootstrap import ApplicationContainer, build_container
from engine.config import Settings
from engine.exceptions import CropNotFoundError
from integrations.storage import PrivateFilesystemStorage
from services.audit import AuditService
from services.auth import AuthService
from services.education import EducationService
from services.knowledge_admin import KnowledgeAdminService
from services.media import MediaService
from services.notifications import NotificationService
from services.privacy import PrivacyService
from services.retention import RetentionService


def create_app(
    settings: Settings | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_container = container or build_container(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if resolved_container.database is not None:
            resolved_container.database.close()

    app = FastAPI(
        title="Crop-Centered Agricultural Advisory API",
        version=__version__,
        description=(
            "Explainable rule-based advisory engine. Demo knowledge is not production agronomy."
        ),
        lifespan=lifespan,
    )
    app.state.container = resolved_container
    auth_service = AuthService(
        resolved_settings.auth_secret,
        resolved_settings.auth_store_path,
        resolved_settings.auth_token_ttl_seconds,
    )
    bootstrap_admin_password = resolved_settings.admin_password
    if bootstrap_admin_password is None and resolved_settings.environment != "production":
        bootstrap_admin_password = "change-me-now"
    if bootstrap_admin_password:
        auth_service.ensure_user(
            resolved_settings.admin_username,
            bootstrap_admin_password,
            "admin",
        )
    app.state.auth_service = auth_service
    app.state.education_service = EducationService(resolved_container.knowledge)
    app.state.knowledge_admin = KnowledgeAdminService(resolved_container.knowledge)
    app.state.notification_service = NotificationService(
        resolved_container,
        resolved_settings.auth_store_path.parent / "notifications.json",
    )
    media_storage = PrivateFilesystemStorage(resolved_settings.media_storage_path)
    app.state.media_service = MediaService(
        media_storage,
        resolved_container.database,
        max_bytes=resolved_settings.media_max_bytes,
        retention_days=resolved_settings.media_retention_days,
    )
    app.state.audit_service = AuditService(
        resolved_container.database, resolved_settings.audit_retention_days
    )
    app.state.privacy_service = PrivacyService(resolved_container.database, app.state.media_service)
    app.state.retention_service = RetentionService(
        resolved_container.database, app.state.media_service, resolved_settings
    )

    if resolved_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    @app.exception_handler(CropNotFoundError)
    async def crop_not_found(_: Request, exc: CropNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def invalid_state(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(auth.router)
    app.include_router(mobile.router)
    app.include_router(voice.router)
    app.include_router(sms.router)
    app.include_router(education.router)
    app.include_router(media.router)
    app.include_router(privacy.router)
    app.include_router(notifications.router)
    app.include_router(admin.router)
    app.include_router(system.router)
    app.include_router(dashboard.router)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"service": app.title, "docs": "/docs", "health": "/api/v1/health"}

    return app


app = create_app()


def run() -> None:
    """Run the API with environment-backed settings."""
    settings = Settings.from_env()
    uvicorn.run(
        "api.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
