"""FR-14 education delivery generated from governed T1-T7 knowledge."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from api.security import PrincipalDependency

router = APIRouter(prefix="/api/v1/education", tags=["education"])


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
