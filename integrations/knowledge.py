"""Filesystem adapter for Developer 2 JSON knowledge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import ValidationError

from engine.exceptions import KnowledgeValidationError
from engine.models.domain import AgriculturalContext, CropProfile, Rule
from engine.models.enums import RuleStatus, TreeId


KnowledgeModel = TypeVar("KnowledgeModel", CropProfile, Rule)

RULE_DIRECTORIES: tuple[tuple[str, TreeId | None], ...] = (
    ("rules", None),
    ("soils", TreeId.SOIL),
    ("regional", TreeId.REGION),
    ("topography", TreeId.TOPOGRAPHY),
    ("climate", TreeId.WEATHER),
    ("timing", TreeId.TIMING),
    ("practices", TreeId.PRACTICES_RISKS),
    ("risks", TreeId.PRACTICES_RISKS),
)


class JSONKnowledgeProvider:
    """Load versioned crop profiles and rules through the shared Pydantic contract."""

    def __init__(self, root: Path | str, allowed_statuses: set[str] | frozenset[str]) -> None:
        self.root = Path(root)
        self.allowed_statuses = {RuleStatus(value) for value in allowed_statuses}
        self._crops: dict[str, CropProfile] = {}
        self._rules: dict[str, Rule] = {}
        self._version: dict[str, Any] = {}
        self.reload()

    @property
    def loaded(self) -> bool:
        return bool(self._crops)

    def reload(self) -> None:
        if not self.root.exists() or not self.root.is_dir():
            raise KnowledgeValidationError(f"knowledge path does not exist: {self.root}")

        crops: dict[str, CropProfile] = {}
        rules: dict[str, Rule] = {}
        candidate_ids: set[str] = set()
        for path in sorted((self.root / "crops").glob("*.json")):
            profile = self._parse(CropProfile, path, self._read_json(path))
            if profile.crop_id in crops:
                raise KnowledgeValidationError(f"duplicate crop_id {profile.crop_id}: {path}")
            if profile.status in self.allowed_statuses:
                crops[profile.crop_id] = profile

        rule_paths = sorted(
            (path, expected_domain)
            for directory, expected_domain in RULE_DIRECTORIES
            for path in (self.root / directory).glob("*.json")
        )
        for path, expected_domain in rule_paths:
            raw = self._read_json(path)
            raw_rules = raw.get("rules") if isinstance(raw, dict) else raw
            if not isinstance(raw_rules, list):
                raise KnowledgeValidationError(f"rule file must contain a JSON list: {path}")
            for index, item in enumerate(raw_rules):
                rule = self._parse(Rule, path, item, item_index=index)
                if expected_domain is not None and rule.domain is not expected_domain:
                    raise KnowledgeValidationError(
                        f"folder {path.parent.name} requires domain "
                        f"{expected_domain.value}, got {rule.domain.value}: {path}"
                    )
                if rule.rule_id in rules:
                    raise KnowledgeValidationError(f"duplicate rule_id {rule.rule_id}: {path}")
                if rule.candidate.candidate_id in candidate_ids:
                    raise KnowledgeValidationError(
                        f"duplicate candidate_id {rule.candidate.candidate_id}: {path}"
                    )
                if rule.status in self.allowed_statuses:
                    rules[rule.rule_id] = rule
                    candidate_ids.add(rule.candidate.candidate_id)

        for rule in rules.values():
            if rule.crop_id != "*" and rule.crop_id not in crops:
                raise KnowledgeValidationError(
                    f"rule {rule.rule_id} references unavailable crop {rule.crop_id}"
                )

        version_path = self.root / "version.json"
        self._version = self._read_json(version_path) if version_path.exists() else {}
        self._crops = crops
        self._rules = rules

    def get_crop_profile(self, crop_id: str) -> CropProfile | None:
        profile = self._crops.get(crop_id)
        return profile.model_copy(deep=True) if profile else None

    def list_crop_profiles(self) -> list[CropProfile]:
        return [self._crops[key].model_copy(deep=True) for key in sorted(self._crops)]

    def get_relevant_rules(
        self,
        crop_id: str,
        context: AgriculturalContext,
        trees: list[TreeId],
    ) -> list[Rule]:
        del context
        tree_set = set(trees)
        selected = [
            rule
            for rule in self._rules.values()
            if rule.crop_id in {crop_id, "*"} and rule.domain in tree_set
        ]
        selected.sort(
            key=lambda rule: (
                list(TreeId).index(rule.domain),
                -rule.priority,
                rule.rule_id,
            )
        )
        return [rule.model_copy(deep=True) for rule in selected]

    def metadata(self) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for rule in self._rules.values():
            status_counts[rule.status.value] = status_counts.get(rule.status.value, 0) + 1
        return {
            **self._version,
            "path": str(self.root),
            "crop_count": len(self._crops),
            "rule_count": len(self._rules),
            "rule_status_counts": status_counts,
            "allowed_statuses": sorted(status.value for status in self.allowed_statuses),
        }

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            with path.open(encoding="utf-8") as stream:
                return json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            raise KnowledgeValidationError(f"cannot read valid JSON from {path}: {exc}") from exc

    @staticmethod
    def _parse(
        model: type[KnowledgeModel],
        path: Path,
        value: Any,
        item_index: int | None = None,
    ) -> KnowledgeModel:
        try:
            return model.model_validate(value)
        except ValidationError as exc:
            suffix = f" item {item_index}" if item_index is not None else ""
            raise KnowledgeValidationError(f"invalid knowledge in {path}{suffix}: {exc}") from exc
