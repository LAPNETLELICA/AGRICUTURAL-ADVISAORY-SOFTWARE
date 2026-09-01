"""Crop catalogue, recommendation retrieval, health, and version endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from api.dependencies import ContainerDependency
from engine import __version__
from engine.models.domain import CropProfile
from engine.models.responses import (
    HealthResponse,
    RecommendationDetail,
)


router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationDetail)
def get_recommendation(
    recommendation_id: str,
    container: ContainerDependency,
) -> RecommendationDetail:
    recommendation = container.recommendations.get(recommendation_id)
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="recommendation not found",
        )
    trace = container.traces.get(recommendation.trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trace not found")
    return RecommendationDetail(recommendation=recommendation, trace=trace)


@router.get("/crops", response_model=list[CropProfile])
def list_crops(
    container: ContainerDependency,
) -> list[CropProfile]:
    return container.knowledge.list_crop_profiles()


@router.get("/crops/{crop_id}", response_model=CropProfile)
def get_crop(
    crop_id: str,
    container: ContainerDependency,
) -> CropProfile:
    crop = container.knowledge.get_crop_profile(crop_id)
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="crop not found")
    return crop


@router.get("/health", response_model=HealthResponse)
def health(
    container: ContainerDependency,
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=container.settings.environment,
        knowledge_loaded=container.knowledge.loaded,
    )


@router.get("/knowledge/version", response_model=dict[str, Any])
def knowledge_version(
    container: ContainerDependency,
) -> dict[str, Any]:
    return container.knowledge.metadata()
