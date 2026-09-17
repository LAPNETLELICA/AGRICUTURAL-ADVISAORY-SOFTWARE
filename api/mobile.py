"""Interactive Mobile advisory endpoint."""

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest
from engine.models.responses import Recommendation

router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


@router.post("/mobile", response_model=Recommendation)
def mobile_advisory(
    request: MobileAdvisoryRequest,
    http_request: Request,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> Recommendation:
    enforce_owner(principal, request.farmer_id)
    try:
        http_request.app.state.media_service.validate_references(
            request.farmer_id, request.evidence.image_references
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return container.engine.advise(AdvisoryRequest.from_mobile(request))
