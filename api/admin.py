"""Administrative API for dashboard, knowledge imports and provider readiness."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.security import AdminDependency
from integrations.database.contact_repository import AgriculturalContact

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class KnowledgeImport(BaseModel):
    category: str
    filename: str
    content: Any


class ContactPayload(BaseModel):
    name: str
    contact_type: str
    description: str | None = None
    specialization: str | None = None
    category: str | None = None
    crop_ids: list[str] = []
    region: str | None = None
    location: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    verified: bool = False
    active: bool = False


def _contacts(request: Request):
    repository = getattr(request.app.state, "contact_repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail="database persistence is not configured")
    return repository


@router.get("/contacts")
def list_contacts(request: Request, admin: AdminDependency) -> list[dict[str, Any]]:
    del admin
    return [asdict(contact) for contact in _contacts(request).list()]


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactPayload, request: Request, admin: AdminDependency
) -> dict[str, Any]:
    if payload.contact_type not in {"SPECIALIST", "VENDOR"}:
        raise HTTPException(status_code=422, detail="contact_type must be SPECIALIST or VENDOR")
    if payload.active and not any((payload.phone, payload.whatsapp, payload.email)):
        raise HTTPException(status_code=422, detail="active contacts require a contact method")
    contact = AgriculturalContact(contact_id=str(uuid4()), **payload.model_dump())
    _contacts(request).create(contact)
    request.app.state.audit_service.record(
        actor_id=admin.subject, action="contact.create", resource_type="agricultural_contact",
        resource_id=contact.contact_id, details={"fields": list(payload.model_fields_set)},
    )
    return asdict(contact)


@router.post("/contacts/{contact_id}/verification")
def set_contact_verification(
    contact_id: str, verified: bool, request: Request, admin: AdminDependency
) -> dict[str, Any]:
    contact = _contacts(request).update(contact_id, verified=verified)
    if contact is None:
        raise HTTPException(status_code=404, detail="contact not found")
    request.app.state.audit_service.record(
        actor_id=admin.subject,
        action="contact.verify",
        resource_type="agricultural_contact",
        resource_id=contact_id,
        details={"verified": verified},
    )
    return asdict(contact)


@router.post("/contacts/{contact_id}/activation")
def set_contact_activation(
    contact_id: str, active: bool, request: Request, admin: AdminDependency
) -> dict[str, Any]:
    contact = _contacts(request).get(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="contact not found")
    if active and not any((contact.phone, contact.whatsapp, contact.email)):
        raise HTTPException(status_code=422, detail="active contacts require a contact method")
    updated = _contacts(request).update(contact_id, active=active)
    request.app.state.audit_service.record(
        actor_id=admin.subject,
        action="contact.activate",
        resource_type="agricultural_contact",
        resource_id=contact_id,
        details={"active": active},
    )
    return asdict(updated)


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
