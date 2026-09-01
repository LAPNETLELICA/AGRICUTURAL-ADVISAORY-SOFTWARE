from engine.advisory.conflict import ConflictResolver
from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.ranking import Ranker
from engine.advisory.scoring import MobileScoringStrategy


def _ranked(context, make_rule):
    rules = [
        make_rule(
            rule_id="rule.high",
            candidate_id="candidate-high",
            conflict_group="planting-choice",
            score_components={"timing_fit": 3},
            priority=200,
        ),
        make_rule(
            rule_id="rule.low",
            candidate_id="candidate-low",
            conflict_group="planting-choice",
            score_components={"timing_fit": 1},
            priority=100,
        ),
        make_rule(
            rule_id="rule.compatible",
            candidate_id="candidate-compatible",
            score_components={"soil_fit": 2},
        ),
    ]
    evaluations = [RuleEvaluator().evaluate(rule, context) for rule in rules]
    return Ranker().rank(MobileScoringStrategy().score(evaluations, {}))


def test_conflict_resolver_suppresses_loser_and_records_reason(context, make_rule):
    result = ConflictResolver().resolve(_ranked(context, make_rule))
    assert [item.candidate.candidate_id for item in result.active] == [
        "candidate-high",
        "candidate-compatible",
    ]
    assert [item.candidate.candidate_id for item in result.suppressed] == ["candidate-low"]
    assert result.conflicts[0].selected_candidate_id == "candidate-high"
    assert result.conflicts[0].rejected_candidate_ids == ["candidate-low"]


def test_no_conflict_group_keeps_all_candidates(context, make_rule):
    ranked = _ranked(context, make_rule)
    without_groups = [
        item.model_copy(
            update={"candidate": item.candidate.model_copy(update={"conflict_group": None})}
        )
        for item in ranked
    ]
    result = ConflictResolver().resolve(without_groups)
    assert len(result.active) == 3
    assert result.conflicts == []

