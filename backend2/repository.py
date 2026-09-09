from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    DOMAIN_TO_TREE,
    TREE_TO_DOMAIN,
    CandidateDefinition,
    ConditionDefinition,
    ConstraintDefinition,
    CropProfile,
    RuleDefinition,
)

RULE_DIRECTORIES: tuple[str, ...] = (
    "rules",
    "soils",
    "regional",
    "topography",
    "climate",
    "timing",
    "practices",
    "risks",
)


class KnowledgeRepository:
    """Read-only repository for Backend 2 JSON knowledge forest."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[1] / "knowledge")

    def _read_json_file(self, file_path: Path) -> Any:
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    def get_crop_profile(self, crop_id: str) -> CropProfile | None:
        crops_dir = self.root / "crops"
        if not crops_dir.exists():
            return None
        for file in sorted(crops_dir.glob("*.json")):
            data = self._read_json_file(file)
            if isinstance(data, dict) and data.get("crop_id") == crop_id:
                return CropProfile(**data)
        return None

    def get_crop_ids(self) -> list[str]:
        crops_dir = self.root / "crops"
        if not crops_dir.exists():
            return []
        ids: list[str] = []
        for file in sorted(crops_dir.glob("*.json")):
            data = self._read_json_file(file)
            if isinstance(data, dict) and "crop_id" in data:
                ids.append(data["crop_id"])
        return ids

    def get_rules(self) -> list[RuleDefinition]:
        result: list[RuleDefinition] = []
        seen_rule_ids: set[str] = set()

        for directory in RULE_DIRECTORIES:
            dir_path = self.root / directory
            if not dir_path.exists():
                continue
            for file in sorted(dir_path.glob("*.json")):
                payload = self._read_json_file(file)
                if not payload:
                    continue
                if isinstance(payload, dict) and "rules" in payload and isinstance(payload["rules"], list):
                    raw_rules = payload["rules"]
                elif isinstance(payload, list):
                    raw_rules = payload
                elif isinstance(payload, dict) and "rule_id" in payload:
                    raw_rules = [payload]
                else:
                    continue

                for data in raw_rules:
                    rule_id = data.get("rule_id")
                    if not rule_id or rule_id in seen_rule_ids:
                        continue
                    seen_rule_ids.add(rule_id)

                    conditions = [
                        ConditionDefinition(
                            field=c["field"],
                            operator=str(c["operator"]).lower(),
                            value=c.get("value"),
                        )
                        for c in data.get("conditions", [])
                        if "field" in c and "operator" in c
                    ]
                    candidate_data = data.get("candidate", {})
                    constraints = [
                        ConstraintDefinition(
                            constraint_id=c["constraint_id"],
                            condition=ConditionDefinition(
                                field=c["condition"]["field"],
                                operator=str(c["condition"]["operator"]).lower(),
                                value=c["condition"].get("value"),
                            ),
                            kind=c["kind"],
                            effect=c["effect"],
                            penalty=c.get("penalty", 0.0),
                            reason=c.get("reason", ""),
                        )
                        for c in candidate_data.get("constraints", [])
                    ]
                    candidate = CandidateDefinition(
                        candidate_id=candidate_data.get("candidate_id", ""),
                        type=candidate_data.get("type", "advisory"),
                        name=candidate_data.get("name", ""),
                        summary=candidate_data.get("summary", ""),
                        reasons=candidate_data.get("reasons", []),
                        warnings=candidate_data.get("warnings", []),
                        actions=candidate_data.get("actions", []),
                        score_components=candidate_data.get("score_components", {}),
                        conflict_group=candidate_data.get("conflict_group"),
                        constraints=constraints,
                    )
                    domain = data.get("domain") or TREE_TO_DOMAIN.get(data.get("tree", ""), "T1")
                    tree = data.get("tree") or DOMAIN_TO_TREE.get(domain, "profile")

                    result.append(
                        RuleDefinition(
                            rule_id=rule_id,
                            crop_id=data.get("crop_id", "*"),
                            domain=domain,
                            version=data.get("version", "0.1.0"),
                            priority=data.get("priority", 100),
                            status=data.get("status", "draft"),
                            source=data.get("source", {}),
                            conditions=conditions,
                            candidate=candidate,
                            condition_mode=str(data.get("condition_mode", "all")).lower(),
                            requires_trees=data.get("requires_trees", []),
                            tree=tree,
                        )
                    )
        return result

    def get_relevant_rule_definitions(self, crop_id: str, selected_trees: list[Any]) -> list[RuleDefinition]:
        tree_identifiers = set()
        for t in selected_trees:
            val = str(t.value if hasattr(t, "value") else t).lower()
            tree_identifiers.add(val)
            if val.upper() in DOMAIN_TO_TREE:
                tree_identifiers.add(DOMAIN_TO_TREE[val.upper()])
            if val in TREE_TO_DOMAIN:
                tree_identifiers.add(TREE_TO_DOMAIN[val].lower())

        return [
            rule for rule in self.get_rules()
            if rule.crop_id in {crop_id, "*"} and (
                rule.tree.lower() in tree_identifiers
                or rule.domain.lower() in tree_identifiers
            )
        ]
