from __future__ import annotations

from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

from domain.models import AgriculturalRule, SourceDocument
from repositories.cameroon import CameroonKnowledgeRepository
from repositories.rules import RuleRepository
from schemas.knowledge import KnowledgeQuery, KnowledgeQueryResponse, KnowledgeVersion
from services.knowledge_service import KnowledgeService
from sources.catalog import DOCUMENTS


def create_app(root: Path | str | None = None) -> FastAPI:
    repository = CameroonKnowledgeRepository(root)
    rule_repository = RuleRepository(repository.base)
    service = KnowledgeService(repository=repository, rule_repository=rule_repository)

    app = FastAPI(
        title="AgriSense Cameroon Knowledge API",
        version="2.0.0",
        description="Backend 2 : Service canonique et souverain de connaissances agricoles camerounaises (QUOI CONSEILLER).",
    )
    app.state.repository = repository
    app.state.rule_repository = rule_repository
    app.state.knowledge_service = service

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "backend2-knowledge", "scope": "quoi_conseiller"}

    @app.get("/api/v1/knowledge/version", response_model=KnowledgeVersion)
    def knowledge_version() -> KnowledgeVersion:
        return service.version()

    @app.get("/api/v1/crops")
    def list_crops() -> list[dict[str, Any]]:
        return service.list_crops()

    @app.get("/api/v1/crops/{crop_id}")
    def get_crop(crop_id: str) -> dict[str, Any]:
        crop = service.get_crop(crop_id)
        if crop is None:
            raise HTTPException(status_code=404, detail=f"Culture '{crop_id}' introuvable.")
        return crop

    @app.get("/api/v1/regions")
    def list_regions() -> list[dict[str, Any]]:
        return service.list_regions()

    @app.get("/api/v1/regions/{region_id}")
    def get_region(region_id: str) -> dict[str, Any]:
        region = service.get_region(region_id)
        if region is None:
            raise HTTPException(status_code=404, detail=f"Région '{region_id}' introuvable.")
        return region

    @app.get("/api/v1/soils")
    def list_soils() -> list[dict[str, Any]]:
        return service.list_soils()

    @app.get("/api/v1/soils/{soil_id}")
    def get_soil(soil_id: str) -> dict[str, Any]:
        soil = service.get_soil(soil_id)
        if soil is None:
            raise HTTPException(status_code=404, detail=f"Type de sol '{soil_id}' introuvable.")
        return soil

    @app.get("/api/v1/rules", response_model=list[AgriculturalRule])
    def list_rules() -> list[AgriculturalRule]:
        return service.list_rules()

    @app.get("/api/v1/rules/{rule_id}", response_model=AgriculturalRule)
    def get_rule(rule_id: str) -> AgriculturalRule:
        rule = service.get_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail=f"Règle agricole '{rule_id}' introuvable.")
        return rule

    @app.get("/api/v1/sources", response_model=list[SourceDocument])
    def list_sources() -> list[SourceDocument]:
        return list(DOCUMENTS.values())

    @app.get("/api/v1/sources/{source_id}", response_model=SourceDocument)
    def get_source(source_id: str) -> SourceDocument:
        doc = DOCUMENTS.get(source_id)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Source documentaire '{source_id}' introuvable.")
        return doc

    @app.get("/api/v1/knowledge/items/{knowledge_id}")
    def get_knowledge_item(knowledge_id: str) -> dict[str, Any]:
        # Recherche multi-entités
        crop = service.get_crop(knowledge_id)
        if crop:
            return {"type": "crop", "item": crop}
        rule = service.get_rule(knowledge_id)
        if rule:
            return {"type": "rule", "item": rule.model_dump(mode="json")}
        soil = service.get_soil(knowledge_id)
        if soil:
            return {"type": "soil", "item": soil}
        region = service.get_region(knowledge_id)
        if region:
            return {"type": "region", "item": region}
        raise HTTPException(status_code=404, detail=f"Élément de connaissance '{knowledge_id}' introuvable.")

    @app.post("/api/v1/knowledge/query", response_model=KnowledgeQueryResponse)
    def query_knowledge(payload: KnowledgeQuery) -> KnowledgeQueryResponse:
        try:
            return service.query(payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"service": app.title, "docs": "/docs", "health": "/api/v1/health"}

    return app


app = create_app()


def run() -> None:
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
