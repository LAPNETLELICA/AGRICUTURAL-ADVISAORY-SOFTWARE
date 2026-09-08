from engine.advisory.evaluator import RuleEvaluator
from engine.models.enums import EvaluationOutcome, TreeId


def _risk_rule(container, context):
    rules = container.knowledge.get_relevant_rules(
        "irish-potato", context, [TreeId.WEATHER]
    )
    return next(rule for rule in rules if rule.rule_id == "demo.potato.heavy-rain-risk.001")


def test_heavy_rain_rule_includes_july_and_september_boundaries(container, context):
    rule = _risk_rule(container, context)
    for month in (7, 9):
        context.future["month"] = month
        result = RuleEvaluator().evaluate(rule, context)
        assert result.outcome is EvaluationOutcome.MATCHED


def test_heavy_rain_rule_excludes_month_outside_window(container, context):
    context.future["month"] = 6
    result = RuleEvaluator().evaluate(_risk_rule(container, context), context)
    assert result.outcome is EvaluationOutcome.NOT_MATCHED


def test_heavy_rain_rule_requires_weather_evidence(container, context):
    context.present["weather"] = {}
    result = RuleEvaluator().evaluate(_risk_rule(container, context), context)
    assert result.outcome is EvaluationOutcome.INSUFFICIENT
