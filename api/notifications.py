"""Proactive agricultural notification sandbox and Wi-Fi phone receiver support."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.security import AdminDependency, PrincipalDependency, enforce_owner

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class SubscriptionRequest(BaseModel):
    recipient_id: str = Field(pattern=r"^[-A-Za-z0-9_.:]{1,100}$")
    farmer_id: str | None = Field(default=None, pattern=r"^[-A-Za-z0-9_.:]{1,100}$")
    crop_id: str = Field(pattern=r"^[-A-Za-z0-9_.:]{1,100}$")
    region: str = Field(min_length=1, max_length=200)
    locality: str | None = Field(default=None, max_length=200)
    language: str = "en"
    cultivation_period: str | None = Field(default=None, max_length=200)
    current_stage: str | None = Field(default=None, max_length=100)
    enabled: bool = True


@router.post("/subscriptions")
def subscribe(
    payload: SubscriptionRequest, request: Request, principal: PrincipalDependency
) -> dict[str, Any]:
    owner = payload.farmer_id or payload.recipient_id
    enforce_owner(principal, owner)
    try:
        return request.app.state.notification_service.subscribe(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/subscriptions")
def subscriptions(request: Request, admin: AdminDependency) -> list[dict[str, Any]]:
    del admin
    return request.app.state.notification_service.list_subscriptions()


@router.post("/trigger/{recipient_id}")
def trigger(recipient_id: str, request: Request, admin: AdminDependency) -> dict[str, Any]:
    del admin
    try:
        return request.app.state.notification_service.trigger(recipient_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
