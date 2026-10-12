"""Adaptive farmer questionnaire endpoints."""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
from engine.models.requests import AdvisoryRequest

router = APIRouter(prefix="/api/v1/questionnaire", tags=["questionnaire"])


class StartPayload(BaseModel):
    farmer_id: str
    region: str | None = None
    locality: str | None = None
    profile_level: str = "beginner"


class AnswerPayload(StartPayload):
    answer: str = Field(min_length=1, max_length=2000)


class CompletePayload(BaseModel):
    context: dict[str, Any]


@router.post("/start")
def start(payload: StartPayload, request: Request, principal: PrincipalDependency) -> dict[str, Any]:
    enforce_owner(principal, payload.farmer_id)
    step = request.app.state.questionnaire_service.start(
        **payload.model_dump(exclude={"farmer_id"})
    )
    return {"complete": False, "step": step}


@router.post("/answer")
def answer(payload: AnswerPayload, request: Request, principal: PrincipalDependency) -> dict[str, Any]:
    enforce_owner(principal, payload.farmer_id)
    context = payload.model_dump(exclude={"answer", "profile_level"})
    step = request.app.state.questionnaire_service.answer(context, payload.answer)
    return {"complete": False, "step": step}


@router.post("/complete")
def complete(
    payload: CompletePayload, request: Request, container: ContainerDependency,
    principal: PrincipalDependency,
) -> dict[str, Any]:
    farmer_id = str(payload.context.get("farmer_id", ""))
    enforce_owner(principal, farmer_id)
    mobile_request = request.app.state.questionnaire_service.complete(payload.context)
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(mobile_request))
    return {"complete": True, "recommendation": recommendation}
