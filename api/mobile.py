"""Interactive Mobile advisory endpoint."""

from fastapi import APIRouter

from api.dependencies import ContainerDependency
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest
from engine.models.responses import Recommendation


router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


@router.post("/mobile", response_model=Recommendation)
def mobile_advisory(
    request: MobileAdvisoryRequest,
    container: ContainerDependency,
) -> Recommendation:
    return container.engine.advise(AdvisoryRequest.from_mobile(request))
