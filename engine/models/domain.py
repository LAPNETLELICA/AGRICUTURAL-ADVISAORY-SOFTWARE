"""Core domain and rule models.

These models are shared work. They intentionally describe agricultural knowledge
without embedding any agricultural threshold in Python.
"""

from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.models.enums import (
    Channel,
    ConditionMode,
    ConditionOperator,
    ConstraintEffect,
    ConstraintKind,
    EvaluationOutcome,
    RecommendationType,
    RuleStatus,
    TreeId,
)


IDENTIFIER_PATTERN = r"^[-A-Za-z0-9_.:]{1,100}$"
RULE_CROP_PATTERN = r"^(?:\*|[-A-Za-z0-9_.:]{1,100})$"


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceReference(StrictModel):
    title: str = Field(min_length=1, max_length=300)
    uri: str | None = Field(default=None, max_length=1000)
    section: str | None = Field(default=None, max_length=200)
    validated_by: str | None = Field(default=None, max_length=200)
    validated_at: datetime | None = None


class Condition(StrictModel):
    field: str = Field(min_length=1, max_length=200)
    operator: ConditionOperator
    value: Any = None

    @field_validator("field")
    @classmethod
    def validate_field_path(cls, value: str) -> str:
        if value.startswith(".") or value.endswith(".") or ".." in value:
            raise ValueError("condition field must be a valid dotted path")
        return value

    @model_validator(mode="after")
    def validate_operator_value(self) -> Condition:
        value_free = {ConditionOperator.EXISTS, ConditionOperator.NOT_EXISTS}
        if self.operator not in value_free and self.value is None:
            raise ValueError(f"operator {self.operator} requires a value")
        if self.operator is ConditionOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("between requires a two-value list")
        if self.operator in {ConditionOperator.IN, ConditionOperator.NOT_IN}:
            if not isinstance(self.value, (list, tuple, set, frozenset)):
                raise ValueError(f"operator {self.operator} requires a collection")
        return self


class ConstraintSpec(StrictModel):
    constraint_id: str = Field(pattern=IDENTIFIER_PATTERN)
    kind: ConstraintKind
    effect: ConstraintEffect
    condition: Condition
    reason: str = Field(min_length=1, max_length=500)
    penalty: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def validate_effect(self) -> ConstraintSpec:
        if self.kind is ConstraintKind.HARD and self.effect is ConstraintEffect.PENALIZE_IF:
            raise ValueError("hard constraints cannot use penalize_if")
        if self.kind is ConstraintKind.SOFT and self.effect is not ConstraintEffect.PENALIZE_IF:
            raise ValueError("soft constraints must use penalize_if")
        if self.kind is ConstraintKind.SOFT and self.penalty <= 0:
            raise ValueError("soft constraints require a positive penalty")
        return self


class CandidateTemplate(StrictModel):
    candidate_id: str = Field(pattern=IDENTIFIER_PATTERN)
    type: RecommendationType
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=1000)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    conflict_group: str | None = Field(default=None, max_length=100)
    constraints: list[ConstraintSpec] = Field(default_factory=list)

    @field_validator("score_components")
    @classmethod
    def finite_scores(cls, values: dict[str, float]) -> dict[str, float]:
        if any(not isfinite(value) for value in values.values()):
            raise ValueError("score components must be finite")
        return values


class CropProfile(StrictModel):
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    family: str = Field(min_length=1, max_length=200)
    cycle_length_days: int = Field(gt=0, le=3650)
    tolerance_profile: dict[str, Any] = Field(default_factory=dict)
    growth_stages: list[str] = Field(default_factory=list)
    storage_behaviour: str | None = Field(default=None, max_length=500)
    version: str = Field(min_length=1, max_length=50)
    status: RuleStatus
    source: SourceReference

    @model_validator(mode="after")
    def validate_profile_governance(self) -> CropProfile:
        if self.status is RuleStatus.VALIDATED and not self.source.validated_by:
            raise ValueError("validated crop profiles require source.validated_by")
        return self


class Rule(StrictModel):
    rule_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str = Field(pattern=RULE_CROP_PATTERN)
    domain: TreeId
    version: str = Field(min_length=1, max_length=50)
    priority: int = Field(default=0, ge=0, le=1000)
    status: RuleStatus
    source: SourceReference
    condition_mode: ConditionMode = ConditionMode.ALL
    conditions: list[Condition] = Field(default_factory=list)
    candidate: CandidateTemplate
    requires_trees: list[TreeId] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hard_constraint_governance(self) -> Rule:
        has_hard = any(
            constraint.kind is ConstraintKind.HARD
            for constraint in self.candidate.constraints
        )
        if has_hard and self.status not in {RuleStatus.VALIDATED, RuleStatus.TEST_ONLY}:
            raise ValueError("hard constraints require validated knowledge")
        if self.status is RuleStatus.VALIDATED and not self.source.validated_by:
            raise ValueError("validated rules require source.validated_by")
        return self


class AgriculturalContext(StrictModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_description: str | None = Field(default=None, max_length=300)
    channel: Channel
    farmer_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    passport_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    crop_profile: CropProfile | None = None
    region: str | None = Field(default=None, max_length=200)
    locality: str | None = Field(default=None, max_length=200)
    past: dict[str, Any] = Field(default_factory=dict)
    present: dict[str, Any] = Field(default_factory=dict)
    future: dict[str, Any] = Field(default_factory=dict)
    uncertainty: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ConditionEvidence(StrictModel):
    field: str
    operator: ConditionOperator
    expected: Any = None
    actual: Any = None
    matched: bool
    missing: bool = False


class Candidate(StrictModel):
    candidate_id: str = Field(pattern=IDENTIFIER_PATTERN)
    type: RecommendationType
    name: str
    summary: str
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    conflict_group: str | None = None
    constraints: list[ConstraintSpec] = Field(default_factory=list)
    rule_id: str = Field(pattern=IDENTIFIER_PATTERN)
    rule_priority: int
    rule_status: RuleStatus
    source: SourceReference


class RuleEvaluation(StrictModel):
    evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str = Field(pattern=IDENTIFIER_PATTERN)
    outcome: EvaluationOutcome
    evidence: list[ConditionEvidence] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    candidate: Candidate | None = None


class ConstraintDecision(StrictModel):
    candidate_id: str = Field(pattern=IDENTIFIER_PATTERN)
    constraint_id: str = Field(pattern=IDENTIFIER_PATTERN)
    kind: ConstraintKind
    effect: ConstraintEffect
    triggered: bool
    excluded: bool = False
    penalty: float = 0.0
    reason: str
    evidence: ConditionEvidence


class ScoreContribution(StrictModel):
    component: str
    raw_value: float
    weight: float
    contribution: float


class ScoredCandidate(StrictModel):
    candidate: Candidate
    score: float
    breakdown: list[ScoreContribution] = Field(default_factory=list)
    constraint_penalty: float = 0.0
    rank: int | None = None


class ConflictRecord(StrictModel):
    conflict_group: str
    selected_candidate_id: str
    rejected_candidate_ids: list[str]
    reason: str
    selected_rule_priority: int
    rejected_rule_priorities: dict[str, int]


class ConflictResolution(StrictModel):
    active: list[ScoredCandidate] = Field(default_factory=list)
    suppressed: list[ScoredCandidate] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)


class CropPassport(StrictModel):
    passport_id: str = Field(default_factory=lambda: str(uuid4()))
    farmer_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    plot_ref: str = Field(pattern=IDENTIFIER_PATTERN)
    current_stage: str | None = Field(default=None, max_length=100)
    opened_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    stage_history: list[dict[str, Any]] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)
    trace_ids: list[str] = Field(default_factory=list)
