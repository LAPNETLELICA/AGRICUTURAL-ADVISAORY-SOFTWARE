"""Application identity, level, language and vocabulary endpoints."""

from fastapi import APIRouter, Request
from pydantic import Field

from api.security import PrincipalDependency
from engine.models.domain import StrictModel
from services.application_context import ApplicationProfile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class ProfileUpdate(StrictModel):
    identity_type: str = Field(min_length=1, max_length=100)
    knowledge_level: str = Field(min_length=1, max_length=40)
    language: str = Field(min_length=2, max_length=20)
    vocabulary_level: str = Field(min_length=1, max_length=40)


@router.get("/me")
def profile_context(request: Request, principal: PrincipalDependency) -> dict[str, object]:
    return request.app.state.application_context.context(principal.subject)


@router.put("/me")
def update_profile(
    payload: ProfileUpdate, request: Request, principal: PrincipalDependency
) -> dict[str, object]:
    profile = request.app.state.application_context.save(
        ApplicationProfile(user_id=principal.subject, **payload.model_dump())
    )
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="profile.update",
        resource_type="user_profile",
        resource_id=principal.subject,
        details={
            "identity_type": profile.identity_type,
            "knowledge_level": profile.knowledge_level,
        },
    )
    return request.app.state.application_context.context(principal.subject)
