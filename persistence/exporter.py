"""Import et Export déterministes entre BASE_CONNAISSANCES_AGRICOLES et la base relationnelle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase
from repositories.rules import RuleRepository


class KnowledgeDataExchange:
    """Garantit l'isomorphisme strict : JSON <-> PostgreSQL <-> JSON."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.kb = CameroonKnowledgeBase(root)
        self.rule_repo = RuleRepository(self.kb)

    def export_all_to_relational_payload(self) -> dict[str, list[dict[str, Any]]]:
        """Exporte l'intégralité des 71 fichiers JSON et règles en structures prêtes pour PostgreSQL."""
        crops_payload = []
        for c in self.kb.list_cultures():
            cycle = c.get("cycle_jours", {})
            crops_payload.append({
                "crop_id": c.get("code"),
                "code": c.get("code"),
                "nom_courant": c.get("nom_courant"),
                "nom_scientifique": c.get("nom_scientifique"),
                "famille_code": c.get("famille_code"),
                "cycle_optimal_jours": cycle.get("optimal", 90),
                "data": c,
            })

        regions_payload = []
        for r in self.kb.list_regions():
            regions_payload.append({
                "region_id": r.get("code"),
                "code": r.get("code"),
                "nom": r.get("nom"),
                "chef_lieu": r.get("chef_lieu", ""),
                "data": r,
            })

        soils_payload = []
        for s in self.kb.list_sols():
            soils_payload.append({
                "soil_id": s.get("code"),
                "code": s.get("code"),
                "nom": s.get("nom"),
                "fao_code": s.get("code_fao", ""),
                "data": s,
            })

        rules_payload = []
        for rule in self.rule_repo.list_rules():
            rules_payload.append({
                "rule_id": rule.rule_id,
                "crop_id": rule.crop_id,
                "tree": rule.tree.value,
                "domain": rule.domain,
                "priority": rule.priority,
                "status": rule.status.value,
                "conditions": [c.model_dump() for c in rule.conditions],
                "candidate": rule.candidate.model_dump(),
                "source_refs": [s.model_dump() for s in rule.source_refs],
                "data": rule.model_dump(mode="json"),
            })

        return {
            "crops": crops_payload,
            "regions": regions_payload,
            "soils": soils_payload,
            "rules": rules_payload,
        }

    def dump_snapshot_to_json(self, output_path: Path | str) -> Path:
        """Génère un export déterministe JSON de la base relationnelle."""
        path = Path(output_path)
        payload = self.export_all_to_relational_payload()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return path
