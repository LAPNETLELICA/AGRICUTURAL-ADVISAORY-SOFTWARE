from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.ranking import Ranker
from engine.advisory.scoring import MobileScoringStrategy


def _scored(context, make_rule, candidate_id, score, priority=100):
    evaluation = RuleEvaluator().evaluate(
        make_rule(
            rule_id=f"rule.{candidate_id}",
            candidate_id=candidate_id,
            score_components={"crop_fit": score},
            priority=priority,
        ),
        context,
    )
    return MobileScoringStrategy().score([evaluation], {})[0]


def test_ranker_orders_score_then_priority_then_identifier(context, make_rule):
    candidates = [
        _scored(context, make_rule, "candidate-c", 1, 100),
        _scored(context, make_rule, "candidate-b", 2, 50),
        _scored(context, make_rule, "candidate-a", 2, 50),
        _scored(context, make_rule, "candidate-d", 2, 80),
    ]
    ranked = Ranker().rank(candidates)
    assert [item.candidate.candidate_id for item in ranked] == [
        "candidate-d",
        "candidate-a",
        "candidate-b",
        "candidate-c",
    ]
    assert [item.rank for item in ranked] == [1, 2, 3, 4]

