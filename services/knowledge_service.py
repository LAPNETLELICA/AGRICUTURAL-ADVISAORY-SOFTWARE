from __future__ import annotations

from typing import Any

from domain.aliases import normalize_crop_id, normalize_region_id, normalize_soil_id
from domain.models import AgriculturalRule, SourceReference
from publication.releases import ReleaseManager
from repositories.cameroon import CameroonKnowledgeRepository
from repositories.rules import RuleRepository
from schemas.knowledge import KnowledgeQuery, KnowledgeQueryResponse, KnowledgeVersion
from sources.catalog import get_source_reference


class KnowledgeService:
    """Service applicatif exposant les connaissances agricoles, règles T1-T7 et releases."""

    def __init__(
        self,
        repository: CameroonKnowledgeRepository | None = None,
        rule_repository: RuleRepository | None = None,
        release_manager: ReleaseManager | None = None,
    ) -> None:
        self.repository = repository or CameroonKnowledgeRepository()
        self.rule_repository = rule_repository or RuleRepository(self.repository.base)
        self.release_manager = release_manager or ReleaseManager(self.repository.base.root)

    def version(self) -> KnowledgeVersion:
        release = self.release_manager.get_active_release()
        stats = {k: int(v) for k, v in self.repository.summary().items() if isinstance(v, int)}
        stats["total_rules"] = len(self.rule_repository.list_rules())

        return KnowledgeVersion(
            knowledge_release=release.release_id,
            schema_version=release.schema_version,
            status=release.status.value,
            release_date=release.release_date.isoformat(),
            sha256_hash=release.sha256_hash,
            author=release.author,
            statistics=stats,
            sources=release.sources,
        )

    def list_crops(self) -> list[dict[str, Any]]:
        return self.repository.list_crops()

    def get_crop(self, crop_id: str) -> dict[str, Any] | None:
        return self.repository.get_crop(crop_id)

    def list_regions(self) -> list[dict[str, Any]]:
        return self.repository.list_regions()

    def get_region(self, region_id: str) -> dict[str, Any] | None:
        return self.repository.get_region(region_id)

    def list_soils(self) -> list[dict[str, Any]]:
        return self.repository.list_soils()

    def get_soil(self, soil_id: str) -> dict[str, Any] | None:
        return self.repository.get_soil(soil_id)

    def list_rules(self) -> list[AgriculturalRule]:
        return self.rule_repository.list_rules()

    def get_rule(self, rule_id: str) -> AgriculturalRule | None:
        return self.rule_repository.get_rule(rule_id)

    def query(self, request: KnowledgeQuery) -> KnowledgeQueryResponse:
        canonical_crop = normalize_crop_id(request.crop_id)
        crop = self.repository.get_crop(canonical_crop)
        if crop is None:
            raise KeyError(f"Culture introuvable : {request.crop_id}")

        resolved = self.repository.resolve_crop(canonical_crop)
        release = self.release_manager.get_active_release()

        # 1. Règles éligibles via RuleRepository
        rules = self.rule_repository.query_rules(
            crop_id=canonical_crop,
            trees=request.trees,
            region_id=request.region_id,
            soil_id=request.soil_id,
        )

        # 2. Collecte des sources documentaires associées
        seen_source_ids = set()
        sources: list[SourceReference] = []
        for r in rules:
            for s in r.source_refs:
                if s.source_id not in seen_source_ids:
                    seen_source_ids.add(s.source_id)
                    sources.append(s)

        # 3. Données contextuelles complémentaires découpées par arbres T1-T7
        tree_set = set(request.trees)
        data: dict[str, Any] = {}

        if "T1" in tree_set:
            data["T1"] = {
                "culture": crop,
                "varietes": resolved.get("varietes", []),
            }
        if "T2" in tree_set:
            data["T2"] = {
                "sols_favorables": resolved.get("sols_favorables", []),
                "caracteristiques_sol": self.repository.base.get_caracteristiques_sol(),
            }
        if "T3" in tree_set:
            regions = resolved.get("regions_principales", [])
            if request.region_id:
                region = self.repository.get_region(request.region_id)
                regions = [region] if region else []
            data["T3"] = {"regions": regions}
        if "T4" in tree_set:
            data["T4"] = self.repository.base.get_topographie()
        if "T5" in tree_set:
            data["T5"] = {
                "zones_agroecologiques": self.repository.base.list_zones_climatiques(),
            }
        if "T6" in tree_set:
            canonical_reg = normalize_region_id(request.region_id) if request.region_id else None
            if canonical_reg is None:
                linked = resolved.get("regions_principales", [])
                canonical_reg = linked[0].get("code") if linked else None
            data["T6"] = {
                "region_id": canonical_reg,
                "calendrier": self.repository.base.get_calendrier_region(canonical_reg) if canonical_reg else None,
            }
        if "T7" in tree_set:
            data["T7"] = {
                "engrais_recommandes": resolved.get("engrais_recommandes", []),
                "ravageurs": resolved.get("ravageurs", []),
            }

        return KnowledgeQueryResponse(
            knowledge_release=release.release_id,
            crop_id=canonical_crop,
            requested_trees=request.trees,
            rules=rules,
            sources=sources,
            data=data,
        )
