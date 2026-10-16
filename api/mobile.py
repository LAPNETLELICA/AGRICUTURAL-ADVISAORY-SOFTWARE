"""Interactive Mobile advisory endpoint."""

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest
from engine.models.responses import Recommendation
from services.presentation import adapt_recommendation

router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


@router.post("/mobile", response_model=Recommendation)
def mobile_advisory(
    request: MobileAdvisoryRequest,
    http_request: Request,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> Recommendation:
    enforce_owner(principal, request.farmer_id)
    previous_id = request.metadata.get("previous_recommendation_id")
    if previous_id is not None:
        if not isinstance(previous_id, str):
            raise HTTPException(
                status_code=422, detail="previous_recommendation_id must be a string"
            )
        previous = container.recommendations.get(previous_id)
        if previous is None:
            raise HTTPException(status_code=404, detail="previous recommendation not found")
        previous_trace = container.traces.get(previous.trace_id)
        if previous_trace is None:
            raise HTTPException(status_code=404, detail="previous recommendation trace not found")
        if previous_trace.context_used.get("farmer_id") != request.farmer_id:
            raise HTTPException(
                status_code=403, detail="previous recommendation ownership required"
            )
        if container.knowledge.normalize_crop_id(
            previous.crop_id
        ) != container.knowledge.normalize_crop_id(request.crop_id or ""):
            raise HTTPException(
                status_code=422, detail="previous recommendation is for another crop"
            )
        request = request.model_copy(
            update={
                "metadata": {
                    **request.metadata,
                    "avoid_candidate_id": previous.primary.candidate_id,
                }
            }
        )
    try:
        http_request.app.state.media_service.validate_references(
            request.farmer_id, request.evidence.image_references
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    visual_evidence: list[dict[str, object]] = []
    for image_id in request.evidence.image_references:
        result = http_request.app.state.image_analysis_service.analyze(
            farmer_id=request.farmer_id,
            image_id=image_id,
            analysis_type="crop",
            crop_id=request.crop_id,
        )
        if not result.relevant:
            raise HTTPException(status_code=422, detail=result.summary)
        visual_evidence.append(http_request.app.state.image_analysis_service.public(result))
    if visual_evidence:
        request = request.model_copy(
            update={
                "evidence": request.evidence.model_copy(update={"visual_evidence": visual_evidence})
            }
        )
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    action_guidance_service = http_request.app.state.action_guidance_service
    contact_service = http_request.app.state.contact_recommendation_service
    recommendation = recommendation.model_copy(
        update={
            "action_guidance": action_guidance_service.resolve(recommendation),
            "contact_recommendation": contact_service.evaluate(recommendation, visual_evidence),
        }
    )
    profile = http_request.app.state.application_context.get(principal.subject)
    return adapt_recommendation(recommendation, profile)
