"""Farmer privacy, export and erasure endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.security import PrincipalDependency
from services.privacy import PrivacyService

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


def _service(request: Request) -> PrivacyService:
    service: PrivacyService = request.app.state.privacy_service
    return service


@router.get("/me")
def privacy_summary(request: Request, principal: PrincipalDependency) -> dict[str, object]:
    settings = request.app.state.container.settings
    return {
        "subject": principal.subject,
        "role": principal.role,
        "retention_days": {
            "trace_and_recommendation": settings.trace_retention_days,
            "history": settings.history_retention_days,
            "sms": settings.sms_retention_days,
            "image": settings.media_retention_days,
            "audit": settings.audit_retention_days,
        },
        "image_evidence": "private, authenticated access only; no V1 disease classification",
    }


@router.get("/export")
def export_my_data(request: Request, principal: PrincipalDependency) -> dict[str, object]:
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="privacy.export",
        resource_type="farmer_data",
        resource_id=principal.subject,
    )
    return _service(request).export_farmer(principal.subject)


@router.delete("/me")
def delete_my_data(
    request: Request,
    principal: PrincipalDependency,
    confirm: str,
) -> dict[str, object]:
    if confirm != "DELETE":
        raise HTTPException(status_code=400, detail='confirm must equal "DELETE"')
    result = _service(request).delete_farmer(principal.subject)
    if principal.role == "farmer":
        request.app.state.auth_service.delete_user(principal.subject)
    # Record after data erasure. Audit events follow their own retention period.
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="privacy.delete",
        resource_type="farmer_data",
        resource_id=principal.subject,
        details=result.to_dict(),
    )
    return {"deleted": result.to_dict()}
