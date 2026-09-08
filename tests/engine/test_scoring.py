from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.scoring import (
    MobileScoringStrategy,
    SMSPriorityScoringStrategy,
)


def test_mobile_score_uses_only_mobile_components(context, make_rule):
    rule = make_rule(
        score_components={
            "crop_fit": 2.0,
            "soil_fit": 3.0,
            "weather_change_urgency": 99.0,
            "risk_penalties": 1.0,
        }
    )
    evaluation = RuleEvaluator().evaluate(rule, context)
    scored = MobileScoringStrategy().score([evaluation], {})[0]
    assert scored.score == 4.0
    assert {item.component for item in scored.breakdown} == {
        "crop_fit",
        "soil_fit",
        "risk_penalties",
    }


def test_sms_priority_uses_only_sms_components(context, make_rule):
    rule = make_rule(
        score_components={
            "crop_fit": 99.0,
            "weather_change_urgency": 3.0,
            "future_risk": 2.0,
        }
    )
    evaluation = RuleEvaluator().evaluate(rule, context)
    scored = SMSPriorityScoringStrategy().score([evaluation], {})[0]
    assert scored.score == 5.0


def test_configurable_weight_and_constraint_penalty(context, make_rule):
    evaluation = RuleEvaluator().evaluate(
        make_rule(score_components={"crop_fit": 2.0}), context
    )
    scored = MobileScoringStrategy(weights={"crop_fit": 1.5}).score(
        [evaluation], {"test.candidate.1": 1.0}
    )[0]
    assert scored.score == 2.0
    assert scored.constraint_penalty == 1.0

