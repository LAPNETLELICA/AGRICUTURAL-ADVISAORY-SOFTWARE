"""Generic, data-driven rule evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from engine.models.domain import (
    AgriculturalContext,
    Candidate,
    Condition,
    ConditionEvidence,
    Rule,
    RuleEvaluation,
)
from engine.models.enums import (
    ConditionMode,
    ConditionOperator,
    EvaluationOutcome,
)


_MISSING = object()


def resolve_field(source: Any, dotted_path: str) -> Any:
    """Resolve a safe dotted field path without evaluating code."""

    current = source.model_dump(mode="python") if isinstance(source, BaseModel) else source
    for part in dotted_path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


class RuleEvaluator:
    """Evaluate the declarative condition language against a crop context."""

    def evaluate_condition(
        self,
        condition: Condition,
        context: AgriculturalContext,
    ) -> ConditionEvidence:
        actual = resolve_field(context, condition.field)
        missing = actual is _MISSING or actual is None
        matched = self._matches(condition, actual, missing)
        return ConditionEvidence(
            field=condition.field,
            operator=condition.operator,
            expected=condition.value,
            actual=None if actual is _MISSING else actual,
            matched=matched,
            missing=missing,
        )

    def evaluate(self, rule: Rule, context: AgriculturalContext) -> RuleEvaluation:
        evidence = [self.evaluate_condition(condition, context) for condition in rule.conditions]
        missing_fields = sorted({item.field for item in evidence if item.missing})

        if not evidence:
            outcome = EvaluationOutcome.MATCHED
        elif rule.condition_mode is ConditionMode.ALL:
            present_failures = [item for item in evidence if not item.matched and not item.missing]
            if all(item.matched for item in evidence):
                outcome = EvaluationOutcome.MATCHED
            elif present_failures:
                outcome = EvaluationOutcome.NOT_MATCHED
            else:
                outcome = EvaluationOutcome.INSUFFICIENT
        elif any(item.matched for item in evidence):
            outcome = EvaluationOutcome.MATCHED
        elif missing_fields:
            outcome = EvaluationOutcome.INSUFFICIENT
        else:
            outcome = EvaluationOutcome.NOT_MATCHED

        candidate = self._candidate(rule) if outcome is EvaluationOutcome.MATCHED else None
        return RuleEvaluation(
            rule_id=rule.rule_id,
            outcome=outcome,
            evidence=evidence,
            missing_fields=missing_fields,
            candidate=candidate,
        )

    @staticmethod
    def _candidate(rule: Rule) -> Candidate:
        template = rule.candidate
        return Candidate(
            candidate_id=template.candidate_id,
            type=template.type,
            name=template.name,
            summary=template.summary,
            reasons=template.reasons,
            warnings=template.warnings,
            actions=template.actions,
            score_components=template.score_components,
            conflict_group=template.conflict_group,
            constraints=template.constraints,
            rule_id=rule.rule_id,
            rule_priority=rule.priority,
            rule_status=rule.status,
            source=rule.source,
        )

    @staticmethod
    def _matches(condition: Condition, actual: Any, missing: bool) -> bool:
        operator = condition.operator
        expected = condition.value
        if operator is ConditionOperator.EXISTS:
            return not missing
        if operator is ConditionOperator.NOT_EXISTS:
            return missing
        if missing:
            return False

        try:
            if operator is ConditionOperator.EQ:
                return bool(actual == expected)
            if operator is ConditionOperator.NE:
                return bool(actual != expected)
            if operator is ConditionOperator.GT:
                return bool(actual > expected)
            if operator is ConditionOperator.GTE:
                return bool(actual >= expected)
            if operator is ConditionOperator.LT:
                return bool(actual < expected)
            if operator is ConditionOperator.LTE:
                return bool(actual <= expected)
            if operator is ConditionOperator.IN:
                return bool(actual in expected)
            if operator is ConditionOperator.NOT_IN:
                return bool(actual not in expected)
            if operator is ConditionOperator.CONTAINS:
                return isinstance(actual, (Sequence, Mapping)) and expected in actual
            if operator is ConditionOperator.BETWEEN:
                lower, upper = expected
                return bool(lower <= actual <= upper)
        except (TypeError, ValueError):
            return False
        raise ValueError(f"unsupported condition operator: {operator}")
