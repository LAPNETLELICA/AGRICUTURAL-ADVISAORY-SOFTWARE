"""Adapter that makes the Cameroon knowledge base the engine's sole source.

The source files remain authoritative.  This adapter only translates their
documentary structure into the engine's existing CropProvider/KnowledgeProvider
contracts; it does not maintain a second agricultural knowledge forest.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase
from engine.exceptions import KnowledgeValidationError
from engine.models.domain import (
    AgriculturalContext,
    CandidateTemplate,
    CropProfile,
    Rule,
    SourceReference,
)
from engine.models.enums import RecommendationType, RuleStatus, TreeId

_ALIASES = {
    "tomate": "tomato",
    "tomato": "tomato",
    "pomme-de-terre": "potato",
    "pomme_de_terre": "potato",
    "pomme de terre": "potato",
    "potato": "potato",
    "irish-potato": "potato",
    "irish_potato": "potato",
    "mais": "maize",
    "maïs": "maize",
    "maize": "maize",
    "corn": "maize",
    "haricot": "bean",
    "bean": "bean",
    "manioc": "cassava",
    "cassava": "cassava",
    "bananier plantain": "plantain",
    "bananier-plantain": "plantain",
    "plantain": "plantain",
}


class CameroonKnowledgeProvider:
    """Read only provider backed exclusively by BASE_CONNAISSANCES_AGRICOLES."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self._base: CameroonKnowledgeBase
        self._crops: dict[str, CropProfile] = {}
        self._rules: dict[str, Rule] = {}
        self.reload()

    @property
    def loaded(self) -> bool:
        return bool(self._crops)

    def reload(self) -> None:
        if not (self.root / "CODIFICATION.json").is_file():
            raise KnowledgeValidationError(
                f"Cameroon knowledge base not found or incomplete: {self.root}"
            )
        self._base = CameroonKnowledgeBase(self.root)
        crops: dict[str, CropProfile] = {}
        rules: dict[str, Rule] = {}
        for document in self._base.list_cultures():
            crop_id = self._crop_id(document)
            profile = self._profile(crop_id, document)
            crops[crop_id] = profile
            rules.update(self._rules_for(profile, document))
        if not crops:
            raise KnowledgeValidationError("Cameroon knowledge base contains no crop documents")
        self._crops, self._rules = crops, rules

    def get_crop_profile(self, crop_id: str) -> CropProfile | None:
        profile = self._crops.get(self.normalize_crop_id(crop_id))
        return profile.model_copy(deep=True) if profile else None

    def list_crop_profiles(self) -> list[CropProfile]:
        return [self._crops[key].model_copy(deep=True) for key in sorted(self._crops)]

    def get_relevant_rules(
        self, crop_id: str, context: AgriculturalContext, trees: list[TreeId]
    ) -> list[Rule]:
        del context
        normalized = self.normalize_crop_id(crop_id)
        wanted = set(trees)
        selected = [
            rule
            for rule in self._rules.values()
            if rule.crop_id == normalized and rule.domain in wanted
        ]
        selected.sort(key=lambda rule: (list(TreeId).index(rule.domain), rule.rule_id))
        return [rule.model_copy(deep=True) for rule in selected]

    def metadata(self) -> dict[str, Any]:
        return {
            "source": "BASE_CONNAISSANCES_AGRICOLES",
            "path": str(self.root),
            "crop_count": len(self._crops),
            "rule_count": len(self._rules),
            "cameroon_catalogue": self._base.summary(),
            "read_only": True,
        }

    @staticmethod
    def normalize_crop_id(crop_id: str) -> str:
        return _ALIASES.get(crop_id.strip().lower(), crop_id.strip().lower())

    def _profile(self, crop_id: str, document: dict[str, Any]) -> CropProfile:
        cycle = document.get("cycle_jours", {})
        stages = list((document.get("caracteristiques_cycle") or {}).keys())
        return CropProfile(
            crop_id=crop_id,
            name=str(document.get("nom_courant", crop_id)),
            family=str(document.get("famille_code", "unknown")),
            cycle_length_days=int(cycle.get("optimal") or cycle.get("max") or 1),
            tolerance_profile={
                "needs": document.get("besoins", {}),
                "links": document.get("liens_dossiers", {}),
            },
            growth_stages=stages,
            version=str(document.get("date_mise_a_jour", "cameroon-knowledge-v1")),
            status=RuleStatus.VALIDATED,
            source=self._source(document),
        )

    def _rules_for(self, profile: CropProfile, document: dict[str, Any]) -> dict[str, Rule]:
        links = document.get("liens_dossiers", {})
        crop_code = str(document.get("code", ""))
        soil = self._read(f"SOL/SOL_PAR_CULTURE/sol_{self._file_slug(profile.crop_id)}.json")
        region_names = self._names_for_regions(links.get("regions_principales", []))
        climate = self._climate_details(links.get("zones_climatiques", []))
        calendar = self._calendar_for(profile.crop_id)
        practices = self._practice_actions(links.get("pratiques_cles", []))
        risks = self._risk_actions(crop_code)
        entries = {
            TreeId.CROP_PROFILE: (
                RecommendationType.ADVISORY,
                document.get("conditions_generales", ""),
                [],
                [],
            ),
            TreeId.SOIL: (
                RecommendationType.SOIL_ACTION,
                self._soil_summary(soil),
                self._soil_actions(soil),
                [],
            ),
            TreeId.REGION: (
                RecommendationType.ADVISORY,
                self._join("Recommended regions", region_names),
                [],
                [],
            ),
            TreeId.TOPOGRAPHY: (
                RecommendationType.PRACTICE,
                self._topography_summary(),
                self._topography_actions(),
                [],
            ),
            TreeId.WEATHER: (
                RecommendationType.RISK_ALERT,
                self._join("Climate context", climate),
                [],
                [],
            ),
            TreeId.TIMING: (
                RecommendationType.TIMING,
                self._calendar_summary(calendar),
                self._calendar_actions(calendar),
                [],
            ),
            TreeId.PRACTICES_RISKS: (
                RecommendationType.PRACTICE,
                self._join("Priority practices and risks", practices + risks),
                practices + risks,
                [],
            ),
        }
        result: dict[str, Rule] = {}
        for tree, (kind, summary, actions, warnings) in entries.items():
            rule_id = f"cameroon.{profile.crop_id}.{tree.value.lower()}"
            result[rule_id] = Rule(
                rule_id=rule_id,
                crop_id=profile.crop_id,
                domain=tree,
                version=profile.version,
                priority=100,
                status=RuleStatus.VALIDATED,
                source=profile.source,
                candidate=CandidateTemplate(
                    candidate_id=f"cameroon.{profile.crop_id}.{tree.value.lower()}",
                    type=kind,
                    name=f"{profile.name}: {tree.value}",
                    summary=summary or f"{profile.name} guidance.",
                    actions=actions[:8],
                    warnings=warnings,
                    score_components={"cameroon_knowledge": 1.0},
                ),
            )
        return result

    def _source(self, document: dict[str, Any]) -> SourceReference:
        return SourceReference(
            title=str(document.get("source", "BASE_CONNAISSANCES_AGRICOLES")),
            uri=f"BASE_CONNAISSANCES_AGRICOLES/CULTURE/CULTURES/{document.get('code', '')}.json",
            validated_by="Cameroon knowledge-base validation",
            validated_at=datetime.now(UTC),
        )

    @staticmethod
    def _crop_id(document: dict[str, Any]) -> str:
        name = str(document.get("nom_courant", "")).strip().lower()
        return _ALIASES.get(name, name.replace(" ", "-"))

    def _read(self, relative: str) -> dict[str, Any]:
        path = self.root / relative
        return self._base._read_json(path) or {}

    @staticmethod
    def _file_slug(crop_id: str) -> str:
        return {
            "potato": "pomme_de_terre",
            "maize": "mais",
            "bean": "haricot",
            "cassava": "manioc",
            "plantain": "bananier_plantain",
        }.get(crop_id, crop_id)

    def _names_for_regions(self, codes: list[str]) -> list[str]:
        return [str(item.get("nom")) for code in codes if (item := self._base.get_region(code))]

    def _climate_details(self, codes: list[str]) -> list[str]:
        zones = {str(zone.get("code")): zone for zone in self._base.list_zones_climatiques()}
        return [
            str(zones[code].get("particularite", zones[code].get("nom", "")))
            for code in codes
            if code in zones
        ]

    def _calendar_for(self, crop_id: str) -> dict[str, Any]:
        data = self._read("CALENDRIER_CULTURAL/calendrier_operations_cultures.json")
        return data.get(self._file_slug(crop_id), {})

    def _practice_actions(self, codes: list[str]) -> list[str]:
        actions: list[str] = []
        directory = self.root / "RISQUES_ET_PRATIQUES" / "BONNES_PRATIQUES"
        for path in directory.glob("*.json"):
            data = self._base._read_json(path) or {}
            if data.get("code") in codes:
                actions.extend(str(item) for item in data.get("consignes", []))
        return actions

    def _risk_actions(self, crop_code: str) -> list[str]:
        actions: list[str] = []
        for item in self._base.list_ravageurs(crop_code):
            actions.extend(str(action) for action in item.get("mesures_preventives", []))
        return actions

    @staticmethod
    def _soil_summary(soil: dict[str, Any]) -> str:
        return CameroonKnowledgeProvider._join(
            "Soil requirements",
            [str(soil.get("exigences_pedologiques", {}).get("drainage_requis", ""))],
        )

    @staticmethod
    def _soil_actions(soil: dict[str, Any]) -> list[str]:
        requirements = soil.get("exigences_pedologiques", {})
        return [
            str(item.get("commentaires"))
            for item in requirements.get("sols_favorables", [])
            if item.get("commentaires")
        ]

    def _topography_summary(self) -> str:
        return self._join(
            "Topography", [str(self._base.get_topographie().get("reliefs", {}).get("titre", ""))]
        )

    def _topography_actions(self) -> list[str]:
        data = self._base.get_topographie().get("amenagements", {})
        return [str(item) for item in data.get("mesures", [])]

    @staticmethod
    def _calendar_summary(calendar: dict[str, Any]) -> str:
        return CameroonKnowledgeProvider._join(
            "Cultural calendar",
            [str(value) for value in calendar.values() if isinstance(value, str)],
        )

    @staticmethod
    def _calendar_actions(calendar: dict[str, Any]) -> list[str]:
        return [
            str(value)
            for item in calendar.values()
            if isinstance(item, dict)
            for value in item.values()
            if isinstance(value, str)
        ]

    @staticmethod
    def _join(label: str, values: list[str]) -> str:
        details = "; ".join(value for value in values if value)
        return f"{label}: {details}" if details else label
