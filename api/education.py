"""FR-14 education delivery generated from governed T1-T7 knowledge."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import Field

from api.security import PrincipalDependency
from engine.models.domain import StrictModel

router = APIRouter(prefix="/api/v1/education", tags=["education"])


@router.get("/technical-fiches")
def education_technical_fiches(
    request: Request,
    principal: PrincipalDependency,
    crop_id: str | None = None,
    subject: str | None = None,
) -> list[dict[str, Any]]:
    del principal
    fiches = request.app.state.technical_fiche_service.list_published(
        crop_id=crop_id, subject=subject
    )
    return [
        {
            **asdict(fiche),
            "download_url": f"/api/v1/technical-fiches/{fiche.fiche_id}/download",
        }
        for fiche in fiches
    ]


@router.get("/crops")
def education_crops(request: Request, principal: PrincipalDependency) -> list[dict[str, Any]]:
    del principal
    return [
        {"crop_id": crop.crop_id, "name": crop.name, "family": crop.family, "version": crop.version}
        for crop in request.app.state.container.knowledge.list_crop_profiles()
    ]


@router.get("/crops/{crop_id}")
def crop_curriculum(
    crop_id: str, request: Request, principal: PrincipalDependency
) -> dict[str, Any]:
    del principal
    try:
        return request.app.state.education_service.curriculum(crop_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


class LearnRequest(StrictModel):
    subject: str = Field(min_length=1, max_length=100)


@router.post("/learn/curriculum")
def adaptive_curriculum(
    payload: LearnRequest, request: Request, principal: PrincipalDependency
) -> dict[str, Any]:
    profile = request.app.state.application_context.get(principal.subject)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="complete your profile first"
        )
    return request.app.state.education_service.learning_curriculum(
        subject=payload.subject,
        knowledge_level=profile.knowledge_level,
        language=profile.language,
        vocabulary_level=profile.vocabulary_level,
    )
