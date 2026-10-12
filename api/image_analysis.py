"""Image relevance and visual evidence endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from api.security import PrincipalDependency
from engine.models.domain import StrictModel

router = APIRouter(prefix="/api/v1/image-analysis", tags=["image analysis"])


class AnalysisRequest(StrictModel):
    image_id: str = Field(min_length=1, max_length=100)
    analysis_type: str = Field(default="general", min_length=1, max_length=40)
    crop_id: str | None = Field(default=None, max_length=100)


@router.get("/references")
def visual_references(request: Request, principal: PrincipalDependency) -> list[dict[str, str]]:
    del principal
    return request.app.state.image_analysis_service.reference_index()


@router.post("")
def analyze_image(
    payload: AnalysisRequest, request: Request, principal: PrincipalDependency
) -> dict[str, object]:
    try:
        result = request.app.state.image_analysis_service.analyze(
            farmer_id=principal.subject,
            image_id=payload.image_id,
            analysis_type=payload.analysis_type,
            crop_id=payload.crop_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="image evidence not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return request.app.state.image_analysis_service.public(result)
