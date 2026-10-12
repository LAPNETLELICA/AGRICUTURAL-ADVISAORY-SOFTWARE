"""Proactive SMS advisory and simulator endpoints."""

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
from engine.models.requests import (
    AdvisoryRequest,
    SMSAdvisoryRequest,
    SMSDeliveryRequest,
)
from engine.models.responses import (
    DeliveryReceipt,
    SMSAdvisoryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["sms"])


@router.post("/advisory/sms", response_model=SMSAdvisoryResponse)
def sms_advisory(
    request: SMSAdvisoryRequest,
    http_request: Request,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> SMSAdvisoryResponse:
    owner_id = request.farmer_id or request.recipient_id
    enforce_owner(principal, owner_id)
    try:
        http_request.app.state.media_service.validate_references(
            owner_id, request.evidence.image_references
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    recommendation = container.engine.advise(AdvisoryRequest.from_sms(request))
    message = container.sms_formatter.format(recommendation)
    if request.language.lower() != "en":
        message = container.translator.translate(message, request.language)
    if len(message) > container.settings.sms_max_length:
        message = message[: container.settings.sms_max_length - 1].rstrip() + "…"
    delivery = container.sms.send(
        request.recipient_id,
        request.crop_id,
        message,
        recommendation.recommendation_id,
    )
    return SMSAdvisoryResponse(
        recommendation=recommendation,
        message=message,
        delivery=delivery,
    )


@router.post("/sms/simulate", response_model=DeliveryReceipt)
def simulate_sms(
    request: SMSDeliveryRequest,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> DeliveryReceipt:
    enforce_owner(principal, request.recipient_id)
    return container.sms.send(
        request.recipient_id,
        request.crop_id,
        request.message,
        request.recommendation_id,
    )


@router.get("/sms/inbox/{recipient_id}", response_model=list[DeliveryReceipt])
def virtual_inbox(
    recipient_id: str,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> list[DeliveryReceipt]:
    enforce_owner(principal, recipient_id)
    return container.sms.inbox(recipient_id)
