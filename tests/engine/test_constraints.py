from __future__ import annotations

import pytest
from pydantic import ValidationError

from engine.advisory.constraints import ConstraintProcessor
from engine.advisory.evaluator import RuleEvaluator
from engine.models.domain import Condition, ConstraintSpec
from engine.models.enums import (
    ConstraintEffect,
    ConstraintKind,
    RuleStatus,
)


def _evaluation(rule, context):
    return RuleEvaluator().evaluate(rule, context)


def test_hard_exclude_removes_candidate(context, make_rule):
    constraint = ConstraintSpec(
        constraint_id="hard-1",
        kind=ConstraintKind.HARD,
        effect=ConstraintEffect.EXCLUDE_IF,
        condition=Condition(field="present.soil.drainage", operator="eq", value="poor"),
        reason="Poor drainage is blocked by this test rule.",
    )
    evaluation = _evaluation(make_rule(constraints=[constraint]), context)
    eligible, decisions, _ = ConstraintProcessor().apply([evaluation], context)
    assert eligible == []
    assert decisions[0].excluded is True


def test_hard_require_excludes_missing_evidence(context, make_rule):
    constraint = ConstraintSpec(
        constraint_id="hard-2",
        kind="hard",
        effect="require",
        condition=Condition(field="present.soil.lab_result", operator="exists"),
        reason="A lab result is required by this test rule.",
    )
    evaluation = _evaluation(make_rule(constraints=[constraint]), context)
    eligible, decisions, _ = ConstraintProcessor().apply([evaluation], context)
    assert not eligible
    assert decisions[0].triggered


def test_soft_constraint_adds_penalty(context, make_rule):
    constraint = ConstraintSpec(
        constraint_id="soft-1",
        kind="soft",
        effect="penalize_if",
        condition=Condition(field="present.soil.drainage", operator="eq", value="poor"),
        reason="Soft risk.",
        penalty=2.5,
    )
    evaluation = _evaluation(make_rule(constraints=[constraint]), context)
    eligible, decisions, penalties = ConstraintProcessor().apply([evaluation], context)
    assert eligible == [evaluation]
    assert decisions[0].penalty == 2.5
    assert penalties["test.candidate.1"] == 2.5


def test_draft_rule_cannot_define_hard_constraint(make_rule):
    constraint = ConstraintSpec(
        constraint_id="hard-3",
        kind="hard",
        effect="exclude_if",
        condition=Condition(field="future.month", operator="eq", value=8),
        reason="Test block.",
    )
    with pytest.raises(ValidationError, match="hard constraints require validated knowledge"):
        make_rule(constraints=[constraint], status=RuleStatus.DRAFT)
