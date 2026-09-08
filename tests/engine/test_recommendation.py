from uuid import uuid4

from engine.advisory.conflict import ConflictResolver
from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.ranking import Ranker
from engine.advisory.recommendation import RecommendationBuilder
from engine.advisory.scoring import MobileScoringStrategy
from engine.models.domain import ConflictResolution
from engine.models.enums import TreeId


def test_builder_returns_cautious_result_when_no_candidate(context):
    result = RecommendationBuilder().build(
        context=context,
        resolution=ConflictResolution(),
        selected_trees=[TreeId.CROP_PROFILE],
        trace_id=str(uuid4()),
    )
    assert result.primary.name == "insufficient_evidence"
    assert "no agricultural threshold was inferred" in result.warnings[0]


def test_builder_aggregates_active_candidate_evidence(context, make_rule):
    rules = [
        make_rule(
            rule_id="rule.1",
            candidate_id="candidate-1",
            score_components={"crop_fit": 2},
        ),
        make_rule(
            rule_id="rule.2",
            candidate_id="candidate-2",
            score_components={"soil_fit": 1},
        ),
    ]
    evaluations = [RuleEvaluator().evaluate(rule, context) for rule in rules]
    ranked = Ranker().rank(MobileScoringStrategy().score(evaluations, {}))
    resolution = ConflictResolver().resolve(ranked)
    result = RecommendationBuilder().build(
        context=context,
        resolution=resolution,
        selected_trees=[TreeId.CROP_PROFILE, TreeId.SOIL],
        trace_id=str(uuid4()),
    )
    assert result.primary.candidate_id == "candidate-1"
    assert result.alternatives[0].candidate_id == "candidate-2"
    assert result.reasons == ["reason"]
    assert result.actions == ["action"]
    assert any("Developer 2" in warning for warning in result.warnings)
