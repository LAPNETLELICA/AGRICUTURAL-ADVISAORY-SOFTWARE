"""Admin-only registration management for regional SMS delivery."""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.security import AdminDependency
from engine.sms import CameroonRegion, DeliveryScope

router = APIRouter(prefix="/api/v1/admin/sms", tags=["admin sms"])


class RegistrationPayload(BaseModel):
    phone: str = Field(min_length=1, max_length=40)
    region: str = Field(min_length=1, max_length=30)
    active: bool = True


class BroadcastScopePayload(BaseModel):
    kind: str = Field(pattern="^(region|cameroon)$")
    region: str | None = Field(default=None, max_length=30)


class BroadcastPreviewPayload(BaseModel):
    message: str = Field(min_length=1, max_length=160)
    scope: BroadcastScopePayload


def _scope(payload: BroadcastScopePayload) -> DeliveryScope:
    if payload.kind == "cameroon":
        return DeliveryScope.cameroon()
    if not payload.region:
        raise ValueError("region scope requires a Cameroon region")
    return DeliveryScope.region_scope(CameroonRegion.parse(payload.region))


def _repository(request: Request) -> Any:
    repository = getattr(request.app.state, "sms_admin_repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail="SMS administration requires database persistence")
    return repository


@router.get("/registrations")
def list_registrations(request: Request, admin: AdminDependency) -> list[dict[str, object]]:
    del admin
    return [asdict(item) for item in _repository(request).list_registrations()]


@router.post("/registrations", status_code=status.HTTP_201_CREATED)
def create_registration(
    payload: RegistrationPayload, request: Request, admin: AdminDependency
) -> dict[str, object]:
    try:
        registration = _repository(request).create_registration(**payload.model_dump())
    except ValueError as exc:
        message = str(exc)
        if "already registered" in message:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
        raise HTTPException(status_code=422, detail=message) from exc
    request.app.state.audit_service.record(
        actor_id=admin.subject,
        action="sms.registration.create",
        resource_type="sms_registration",
        resource_id=registration.registration_id,
        details={"region": registration.region.value, "active": registration.active},
    )
    return asdict(registration)


@router.post("/broadcasts/preview")
def preview_broadcast(
    payload: BroadcastPreviewPayload, request: Request, admin: AdminDependency
) -> dict[str, object]:
    del admin
    try:
        scope = _scope(payload.scope)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    recipients = _repository(request).resolve_active_recipients(scope)
    return {
        "recipient_count": len(recipients),
        "scope": scope.kind.value,
        "region": scope.region.value if scope.region else None,
        "message_length": len(payload.message),
    }


@router.post("/broadcasts/send")
def send_broadcast(
    payload: BroadcastPreviewPayload, request: Request, admin: AdminDependency
) -> dict[str, object]:
    try:
        scope = _scope(payload.scope)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    recipients = _repository(request).resolve_active_recipients(scope)
    if not recipients:
        raise HTTPException(status_code=422, detail="no active registrations match this scope")
    sent = failed = 0
    for recipient in recipients:
        delivery_status = "sent"
        try:
            request.app.state.container.sms.send(recipient.phone, "regional-alert", payload.message)
            sent += 1
        except Exception:
            delivery_status = "failed"
            failed += 1
        _repository(request).create_delivery(
            registration_id=recipient.registration_id,
            scope=scope,
            source="manual",
            message=payload.message,
            status=delivery_status,
        )
    request.app.state.audit_service.record(
        actor_id=admin.subject,
        action="sms.broadcast.send",
        resource_type="sms_broadcast",
        details={"sent": sent, "failed": failed, "scope": scope.kind.value},
    )
    return {"sent": sent, "failed": failed, "recipient_count": len(recipients)}


@router.get("/deliveries")
def list_deliveries(request: Request, admin: AdminDependency, limit: int = 100) -> list[dict[str, object]]:
    del admin
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return _repository(request).list_deliveries(limit)
