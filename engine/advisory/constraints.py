"""Validated hard constraints and soft penalty processing."""

from __future__ import annotations

from engine.advisory.evaluator import RuleEvaluator
from engine.models.domain import (
    AgriculturalContext,
    ConstraintDecision,
    RuleEvaluation,
)
from engine.models.enums import ConstraintEffect, ConstraintKind


class ConstraintProcessor:
    def __init__(self, evaluator: RuleEvaluator | None = None) -> None:
        self._evaluator = evaluator or RuleEvaluator()

    def apply(
        self,
        evaluations: list[RuleEvaluation],
        context: AgriculturalContext,
    ) -> tuple[list[RuleEvaluation], list[ConstraintDecision], dict[str, float]]:
        eligible: list[RuleEvaluation] = []
        decisions: list[ConstraintDecision] = []
        penalties: dict[str, float] = {}

        for evaluation in evaluations:
            candidate = evaluation.candidate
            if candidate is None:
                continue
            excluded = False
            for constraint in candidate.constraints:
                evidence = self._evaluator.evaluate_condition(constraint.condition, context)
                if constraint.effect is ConstraintEffect.REQUIRE:
                    triggered = not evidence.matched
                else:
                    triggered = evidence.matched

                constraint_excluded = triggered and constraint.kind is ConstraintKind.HARD
                penalty = constraint.penalty if (
                    triggered and constraint.kind is ConstraintKind.SOFT
                ) else 0.0
                excluded = excluded or constraint_excluded
                penalties[candidate.candidate_id] = (
                    penalties.get(candidate.candidate_id, 0.0) + penalty
                )
                decisions.append(
                    ConstraintDecision(
                        candidate_id=candidate.candidate_id,
                        constraint_id=constraint.constraint_id,
                        kind=constraint.kind,
                        effect=constraint.effect,
                        triggered=triggered,
                        excluded=constraint_excluded,
                        penalty=penalty,
                        reason=constraint.reason,
                        evidence=evidence,
                    )
                )
            if not excluded:
                eligible.append(evaluation)

        return eligible, decisions, penalties
