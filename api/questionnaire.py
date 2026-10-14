"""Adaptive farmer questionnaire endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
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
    language: str = Field(default="en", min_length=2, max_length=20)
    conversation_id: str | None = None


class AnswerPayload(StartPayload):
    answer: str = Field(min_length=1, max_length=2000)


class CompletePayload(BaseModel):
    context: dict[str, Any]
    conversation_id: str | None = None


@router.post("/start")
def start(payload: StartPayload, request: Request, principal: PrincipalDependency) -> dict[str, Any]:
    enforce_owner(principal, payload.farmer_id)
    result = request.app.state.questionnaire_service.start_conversation(
        **payload.model_dump(exclude={"farmer_id", "conversation_id"}), farmer_id=payload.farmer_id
    )
    return {"complete": False, "conversation_id": result.conversation.conversation_id, "step": result.step}


@router.post("/answer")
def answer(
    payload: AnswerPayload,
    request: Request,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> dict[str, Any]:
    enforce_owner(principal, payload.farmer_id)
    conversation_id = payload.conversation_id
    if conversation_id is None:
        active = request.app.state.container.conversations.latest_open(payload.farmer_id)
        if active is None:
            raise HTTPException(status_code=400, detail="No open conversation; call /questionnaire/start first")
        conversation_id = active.conversation_id
    try:
        result = request.app.state.questionnaire_service.receive_message(conversation_id, payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
    if result.conversation.farmer_id != payload.farmer_id:
        raise HTTPException(status_code=403, detail="Conversation does not belong to farmer")
    if result.ready_request is not None:
        recommendation = container.engine.advise(AdvisoryRequest.from_mobile(result.ready_request))
        return {"complete": True, "conversation_id": conversation_id, "recommendation": recommendation}
    return {"complete": False, "conversation_id": conversation_id, "step": result.step}


@router.get("/conversations/{conversation_id}")
def conversation_history(conversation_id: str, request: Request, principal: PrincipalDependency) -> dict[str, Any]:
    try:
        conversation, messages = request.app.state.questionnaire_service.get_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
    enforce_owner(principal, conversation.farmer_id)
    return {"conversation_id": conversation_id, "status": conversation.status, "context": conversation.context, "messages": messages, "recommendation": conversation.recommendation}


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
