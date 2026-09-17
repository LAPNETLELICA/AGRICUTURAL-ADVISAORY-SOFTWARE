"""Administrative API for dashboard, knowledge imports and provider readiness."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.security import AdminDependency

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class KnowledgeImport(BaseModel):
    category: str
    filename: str
    content: Any


@router.get("/overview")
def overview(request: Request, admin: AdminDependency) -> dict[str, Any]:
    del admin
    container = request.app.state.container
    return {
        "environment": container.settings.environment,
        "auth_required": container.settings.auth_required,
        "database": "postgresql" if container.database else "in-memory",
        "knowledge": container.knowledge.metadata(),
        "providers": {
            "weather": container.settings.weather_provider,
            "translation": container.settings.translation_provider,
            "speech": container.settings.speech_provider,
            "sms": container.settings.sms_provider,
        },
        "notifications": len(request.app.state.notification_service.list_subscriptions()),
    }


@router.get("/knowledge")
def knowledge_inventory(request: Request, admin: AdminDependency) -> dict[str, Any]:
    del admin
    return request.app.state.knowledge_admin.inventory()


@router.post("/knowledge/import")
def import_knowledge(
    payload: KnowledgeImport, request: Request, admin: AdminDependency
) -> dict[str, Any]:
    del admin
    try:
        return request.app.state.knowledge_admin.import_document(
            payload.category, payload.filename, payload.content
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/providers")
def provider_status(request: Request, admin: AdminDependency) -> dict[str, Any]:
    del admin
    settings = request.app.state.container.settings
    return {
        "weather": {
            "configured": settings.weather_provider != "disabled",
            "provider": settings.weather_provider,
        },
        "translation": {
            "configured": settings.translation_provider != "passthrough",
            "provider": settings.translation_provider,
        },
        "speech": {
            "configured": settings.speech_provider != "disabled",
            "provider": settings.speech_provider,
        },
        "sms": {
            "configured": settings.sms_provider != "simulator",
            "provider": settings.sms_provider,
        },
        "note": (
            "Provider-specific adapters remain outside the deterministic engine and can be "
            "injected when credentials/APIs are available."
        ),
    }


@router.post("/retention/run")
def run_retention(request: Request, admin: AdminDependency) -> dict[str, Any]:
    result = request.app.state.retention_service.cleanup()
    request.app.state.audit_service.record(
        actor_id=admin.subject,
        action="retention.cleanup",
        resource_type="system",
        details={
            "media": result.media,
            "traces": result.traces,
            "history": result.history,
            "sms": result.sms,
            "audit": result.audit,
        },
    )
    return {
        "media": result.media,
        "traces": result.traces,
        "history": result.history,
        "sms": result.sms,
        "audit": result.audit,
    }
