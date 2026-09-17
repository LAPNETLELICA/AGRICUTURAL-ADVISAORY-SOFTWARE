"""Crop catalogue, recommendation retrieval, health, and version endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
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
    principal: PrincipalDependency,
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
    owner = trace.context_used.get("farmer_id") if isinstance(trace.context_used, dict) else None
    enforce_owner(principal, owner)
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


@router.get("/ready")
def readiness(container: ContainerDependency) -> dict[str, Any]:
    database_ready = True
    migration_ready = True
    migration_version: str | None = None
    if container.database is not None:
        try:
            container.database.ping()
            with container.database.engine.connect() as connection:
                migration_version = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
            migration_ready = migration_version == "9b81c2276e10"
        except Exception:
            database_ready = False
            migration_ready = False
    knowledge = container.knowledge.metadata()
    production_knowledge_ready = bool(knowledge.get("crop_count"))
    ready = (
        database_ready
        and migration_ready
        and (production_knowledge_ready or container.settings.environment != "production")
    )
    return {
        "status": "ready" if ready else "not_ready",
        "database": database_ready,
        "migration": {"ready": migration_ready, "version": migration_version},
        "knowledge": production_knowledge_ready,
        "providers": {
            "weather": container.settings.weather_provider,
            "translation": container.settings.translation_provider,
            "speech": container.settings.speech_provider,
            "sms": container.settings.sms_provider,
        },
    }
