"""Developer 1 engine component contracts."""

from __future__ import annotations

from typing import Protocol

from engine.models.domain import (
    AgriculturalContext,
    ConflictResolution,
    ConstraintDecision,
    Rule,
    RuleEvaluation,
    ScoredCandidate,
)
from engine.models.enums import Channel, TreeId


class CropTreeSelectorContract(Protocol):
    def select(self, context: AgriculturalContext) -> list[TreeId]: ...

    def expand(self, selected: list[TreeId], required: list[TreeId]) -> list[TreeId]: ...


class RuleEvaluatorContract(Protocol):
    def evaluate(self, rule: Rule, context: AgriculturalContext) -> RuleEvaluation: ...


class ConstraintProcessorContract(Protocol):
    def apply(
        self,
        evaluations: list[RuleEvaluation],
        context: AgriculturalContext,
    ) -> tuple[list[RuleEvaluation], list[ConstraintDecision], dict[str, float]]: ...


class ScoringStrategyContract(Protocol):
    channel: Channel

    def score(
        self,
        evaluations: list[RuleEvaluation],
        penalties: dict[str, float],
    ) -> list[ScoredCandidate]: ...


class RankerContract(Protocol):
    def rank(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]: ...


class ConflictResolverContract(Protocol):
    def resolve(self, ranked: list[ScoredCandidate]) -> ConflictResolution: ...

