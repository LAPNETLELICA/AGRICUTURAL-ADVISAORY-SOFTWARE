from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DOMAIN_TO_TREE: dict[str, str] = {
    "T1": "profile",
    "T2": "soil",
    "T3": "region",
    "T4": "topography",
    "T5": "weather",
    "T6": "timing",
    "T7": "practices_risks",
}

TREE_TO_DOMAIN: dict[str, str] = {
    "profile": "T1",
    "soil": "T2",
    "soils": "T2",
    "region": "T3",
    "regional": "T3",
    "topography": "T4",
    "topo": "T4",
    "weather": "T5",
    "climate": "T5",
    "timing": "T6",
    "practices_risks": "T7",
    "practice": "T7",
    "practices": "T7",
    "risk": "T7",
    "risks": "T7",
}


@dataclass(frozen=True)
class ConditionDefinition:
    field: str
    operator: str
    value: Any = None


@dataclass(frozen=True)
class ConstraintDefinition:
    constraint_id: str
    condition: ConditionDefinition
    kind: str
    effect: str
    penalty: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class CandidateDefinition:
    candidate_id: str
    type: str
    name: str
    summary: str
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    score_components: dict[str, float] = field(default_factory=dict)
    conflict_group: str | None = None
    constraints: list[ConstraintDefinition] = field(default_factory=list)


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    crop_id: str
    domain: str
    version: str
    priority: int
    status: str
    source: Any
    conditions: list[ConditionDefinition]
    candidate: CandidateDefinition
    condition_mode: str = "all"
    requires_trees: list[str] = field(default_factory=list)
    tree: str = ""

    def __post_init__(self) -> None:
        if not self.tree:
            object.__setattr__(self, "tree", DOMAIN_TO_TREE.get(self.domain, self.domain.lower()))


@dataclass(frozen=True)
class CropProfile:
    crop_id: str
    name: str
    family: str | None = None
    cycle_length_days: int | None = None
    cycle_days: int | None = None
    growth_stages: list[str] = field(default_factory=list)
    water_needs: str | None = None
    nutrient_needs: str | None = None
    spacing: str | None = None
    tolerances: dict[str, Any] = field(default_factory=dict)
    tolerance_profile: dict[str, Any] = field(default_factory=dict)
    objectives: list[str] = field(default_factory=list)
    storage_behaviour: str | None = None
    storage_behavior: str | None = None
    status: str = "draft"
    validation_status: str = "DEVELOPMENT"
    source: Any = "architecture-v3.0"
    version: str = "0.1.0"

    def __post_init__(self) -> None:
        if self.cycle_days is None and self.cycle_length_days is not None:
            object.__setattr__(self, "cycle_days", self.cycle_length_days)
        elif self.cycle_length_days is None and self.cycle_days is not None:
            object.__setattr__(self, "cycle_length_days", self.cycle_days)

        if not self.tolerances and self.tolerance_profile:
            object.__setattr__(self, "tolerances", self.tolerance_profile)
        elif not self.tolerance_profile and self.tolerances:
            object.__setattr__(self, "tolerance_profile", self.tolerances)

        if not self.storage_behavior and self.storage_behaviour:
            object.__setattr__(self, "storage_behavior", self.storage_behaviour)
        elif not self.storage_behaviour and self.storage_behavior:
            object.__setattr__(self, "storage_behaviour", self.storage_behavior)

        if self.validation_status == "DEVELOPMENT" and self.status != "DEVELOPMENT":
            object.__setattr__(self, "validation_status", self.status)
