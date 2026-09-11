from __future__ import annotations

from typing import Any

from .repository import KnowledgeRepository


class KnowledgeProvider:
    """Backend 2 knowledge provider.

    Public contract intentionally mirrors Backend 1:
        get_relevant_rules(crop_id, context, trees)

    `context` is only used for future extensibility; rule filtering is crop/tree based here,
    while Backend 1 remains responsible for declarative condition evaluation.
    """

    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository or KnowledgeRepository()

    def get_crop_profile(self, crop_id: str):
        return self.repository.get_crop_profile(crop_id)

    def list_crops(self) -> list[str]:
        return self.repository.get_crop_ids()

    def get_relevant_rule_definitions(
        self, crop_id: str, context: Any = None, trees: list[Any] | None = None
    ):
        if trees is None:
            trees = []
        return self.repository.get_relevant_rule_definitions(crop_id, trees)

    def get_relevant_rules(self, crop_id: str, context: Any, trees: list[Any]):
        """Return Backend-1 Rule objects when Backend 1's models are available.

        The exact Backend 1 models were absent from the supplied ZIP. This method therefore
        imports them lazily and constructs them from the stable knowledge schema. If the model
        constructors differ, the integration error is explicit instead of silently corrupting data.
        """
        definitions = self.get_relevant_rule_definitions(crop_id, context, trees)
        try:
            from engine.models.domain import Candidate, Condition, Constraint, Rule
            from engine.models.enums import (
                ConditionMode,
                ConditionOperator,
                ConstraintEffect,
                ConstraintKind,
                RuleStatus,
                TreeId,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Backend 1 contracts are missing. Supply engine/models and engine/interfaces "
                "from Backend 1 before wiring KnowledgeProvider.get_relevant_rules()."
            ) from exc

        def enum_value(enum_cls, value: str):
            try:
                return enum_cls(value)
            except (ValueError, TypeError):
                try:
                    return enum_cls[value]
                except (KeyError, TypeError):
                    return value

        result = []
        for item in definitions:
            conditions = [
                Condition(
                    field=c.field, operator=enum_value(ConditionOperator, c.operator), value=c.value
                )
                for c in item.conditions
            ]
            constraints = [
                Constraint(
                    constraint_id=c.constraint_id,
                    condition=Condition(
                        field=c.condition.field,
                        operator=enum_value(ConditionOperator, c.condition.operator),
                        value=c.condition.value,
                    ),
                    kind=enum_value(ConstraintKind, c.kind),
                    effect=enum_value(ConstraintEffect, c.effect),
                    penalty=c.penalty,
                    reason=c.reason,
                )
                for c in item.candidate.constraints
            ]
            candidate = Candidate(
                candidate_id=item.candidate.candidate_id,
                type=item.candidate.type,
                name=item.candidate.name,
                summary=item.candidate.summary,
                reasons=item.candidate.reasons,
                warnings=item.candidate.warnings,
                actions=item.candidate.actions,
                score_components=item.candidate.score_components,
                conflict_group=item.candidate.conflict_group,
                constraints=constraints,
            )
            tree_target = item.domain if hasattr(item, "domain") and item.domain else item.tree
            result.append(
                Rule(
                    rule_id=item.rule_id,
                    crop_id=item.crop_id,
                    domain=enum_value(TreeId, tree_target),
                    version=item.version,
                    priority=item.priority,
                    status=enum_value(RuleStatus, item.status),
                    source=item.source,
                    conditions=conditions,
                    candidate=candidate,
                    condition_mode=enum_value(ConditionMode, item.condition_mode),
                    requires_trees=[enum_value(TreeId, t) for t in item.requires_trees],
                )
            )
        return result
