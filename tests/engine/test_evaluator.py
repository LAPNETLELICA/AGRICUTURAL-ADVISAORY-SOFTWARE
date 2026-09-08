from __future__ import annotations

import pytest

from engine.advisory.evaluator import RuleEvaluator
from engine.models.domain import Condition
from engine.models.enums import (
    ConditionMode,
    ConditionOperator,
    EvaluationOutcome,
)


@pytest.mark.parametrize(
    ("operator", "actual", "expected", "matched"),
    [
        (ConditionOperator.EQ, 5, 5, True),
        (ConditionOperator.NE, 5, 4, True),
        (ConditionOperator.GT, 5, 4, True),
        (ConditionOperator.GTE, 5, 5, True),
        (ConditionOperator.LT, 5, 6, True),
        (ConditionOperator.LTE, 5, 5, True),
        (ConditionOperator.IN, "heavy", ["light", "heavy"], True),
        (ConditionOperator.NOT_IN, "heavy", ["light"], True),
        (ConditionOperator.CONTAINS, ["spots", "wilting"], "spots", True),
        (ConditionOperator.BETWEEN, 8, [7, 9], True),
        (ConditionOperator.GT, "not-a-number", 4, False),
    ],
)
def test_condition_operators(context, operator, actual, expected, matched):
    context.present["test_value"] = actual
    evidence = RuleEvaluator().evaluate_condition(
        Condition(field="present.test_value", operator=operator, value=expected), context
    )
    assert evidence.matched is matched


def test_empty_rule_matches_and_builds_candidate(context, make_rule):
    result = RuleEvaluator().evaluate(make_rule(), context)
    assert result.outcome is EvaluationOutcome.MATCHED
    assert result.candidate is not None


def test_missing_evidence_is_insufficient(context, make_rule):
    rule = make_rule(
        conditions=[Condition(field="present.missing", operator="eq", value=1)]
    )
    result = RuleEvaluator().evaluate(rule, context)
    assert result.outcome is EvaluationOutcome.INSUFFICIENT
    assert result.missing_fields == ["present.missing"]


def test_present_false_condition_wins_over_missing_in_all_mode(context, make_rule):
    rule = make_rule(
        conditions=[
            Condition(field="present.soil.drainage", operator="eq", value="good"),
            Condition(field="present.missing", operator="eq", value=1),
        ]
    )
    result = RuleEvaluator().evaluate(rule, context)
    assert result.outcome is EvaluationOutcome.NOT_MATCHED


def test_any_mode_matches_when_one_condition_matches(context, make_rule):
    rule = make_rule(
        condition_mode=ConditionMode.ANY,
        conditions=[
            Condition(field="present.missing", operator="eq", value=1),
            Condition(field="future.month", operator="eq", value=8),
        ],
    )
    result = RuleEvaluator().evaluate(rule, context)
    assert result.outcome is EvaluationOutcome.MATCHED


def test_exists_and_not_exists(context):
    evaluator = RuleEvaluator()
    assert evaluator.evaluate_condition(
        Condition(field="present.soil.ph", operator="exists"), context
    ).matched
    assert evaluator.evaluate_condition(
        Condition(field="present.unknown", operator="not_exists"), context
    ).matched

