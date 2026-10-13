from engine.advisory.evaluator import RuleEvaluator
from engine.models.enums import EvaluationOutcome, TreeId


def _weather_rule(container, context):
    rules = container.knowledge.get_relevant_rules("irish-potato", context, [TreeId.WEATHER])
    return next(rule for rule in rules if rule.rule_id == "cameroon.potato.t5")


def test_cameroon_weather_rule_is_available_for_potato(container, context):
    result = RuleEvaluator().evaluate(_weather_rule(container, context), context)
    assert result.outcome is EvaluationOutcome.MATCHED
    assert result.candidate is not None


def test_cameroon_weather_rule_is_not_a_legacy_demo_rule(container, context):
    rule = _weather_rule(container, context)
    assert rule.rule_id.startswith("cameroon.potato.")
    assert rule.domain is TreeId.WEATHER


def test_cameroon_weather_rule_remains_evaluable_without_weather_evidence(container, context):
    context.present["weather"] = {}
    result = RuleEvaluator().evaluate(_weather_rule(container, context), context)
    assert result.outcome is EvaluationOutcome.MATCHED
