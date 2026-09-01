"""Proactive SMS advisory and simulator endpoints."""

from fastapi import APIRouter

from api.dependencies import ContainerDependency
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
    container: ContainerDependency,
) -> SMSAdvisoryResponse:
    recommendation = container.engine.advise(AdvisoryRequest.from_sms(request))
    message = container.sms_formatter.format(recommendation)
    if request.language.lower() != "en":
        message = container.translator.translate(message, request.language)
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
) -> DeliveryReceipt:
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
) -> list[DeliveryReceipt]:
    return container.sms.inbox(recipient_id)
