"""Crop-centered advisory pipeline orchestration."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
from uuid import uuid4

from engine.advisory.conflict import ConflictResolver
from engine.advisory.constraints import ConstraintProcessor
from engine.advisory.context import CropContextBuilder
from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.passport import CropPassportService
from engine.advisory.ranking import Ranker
from engine.advisory.recommendation import RecommendationBuilder
from engine.advisory.scoring import (
    MobileScoringStrategy,
    SMSPriorityScoringStrategy,
)
from engine.advisory.selector import CropTreeSelector
from engine.interfaces.providers import (
    HistoryProvider,
    KnowledgeProvider,
    RecommendationRepository,
    TraceRecorder,
    TransactionManager,
)
from engine.models.domain import AgriculturalContext, Rule, RuleEvaluation, ScoreContribution
from engine.models.enums import Channel, EvaluationOutcome, Objective, TreeId
from engine.models.requests import AdvisoryRequest
from engine.models.responses import (
    CandidateScoreRecord,
    Recommendation,
    TraceRecord,
)


class AdvisoryEngine:
    """Implement the book's evaluate -> constrain -> score -> rank -> resolve flow."""

    def __init__(
        self,
        *,
        context_builder: CropContextBuilder,
        tree_selector: CropTreeSelector,
        knowledge_provider: KnowledgeProvider,
        evaluator: RuleEvaluator,
        constraint_processor: ConstraintProcessor,
        mobile_scoring: MobileScoringStrategy,
        sms_scoring: SMSPriorityScoringStrategy,
        ranker: Ranker,
        conflict_resolver: ConflictResolver,
        recommendation_builder: RecommendationBuilder,
        trace_recorder: TraceRecorder,
        recommendation_repository: RecommendationRepository,
        history_provider: HistoryProvider,
        passport_service: CropPassportService,
        transaction_manager: TransactionManager | None = None,
    ) -> None:
        self._context_builder = context_builder
        self._tree_selector = tree_selector
        self._knowledge_provider = knowledge_provider
        self._evaluator = evaluator
        self._constraint_processor = constraint_processor
        self._mobile_scoring = mobile_scoring
        self._sms_scoring = sms_scoring
        self._ranker = ranker
        self._conflict_resolver = conflict_resolver
        self._recommendation_builder = recommendation_builder
        self._trace_recorder = trace_recorder
        self._recommendation_repository = recommendation_repository
        self._history_provider = history_provider
        self._passport_service = passport_service
        self._transaction_manager = transaction_manager

    def advise(self, request: AdvisoryRequest) -> Recommendation:
        started_at = datetime.now(UTC)
        passport = self._passport_service.open_for_request(request)
        if passport and request.passport_id != passport.passport_id:
            request = request.model_copy(update={"passport_id": passport.passport_id})

        context = self._context_builder.build(request)
        criteria_review = self._review_criteria(context)
        selected_trees = self._tree_selector.select(context)
        rules, evaluations, selected_trees = self._evaluate_forest(context, selected_trees)
        domains = {rule.rule_id: rule.domain for rule in rules}

        eligible, constraint_decisions, penalties = self._constraint_processor.apply(
            evaluations, context
        )
        strategy = self._sms_scoring if context.channel is Channel.SMS else self._mobile_scoring
        scored = strategy.score(eligible, penalties)
        objective_tree = {
            Objective.SOIL_IMPROVEMENT: TreeId.SOIL,
            Objective.SUITABILITY: TreeId.REGION,
            Objective.PLANTING: TreeId.TIMING,
            Objective.RISK: TreeId.PRACTICES_RISKS,
            Objective.YIELD_IMPROVEMENT: TreeId.PRACTICES_RISKS,
            Objective.EDUCATION: TreeId.CROP_PROFILE,
            Objective.CROP_DISCOVERY: TreeId.CROP_PROFILE,
        }.get(request.objective)
        if objective_tree is not None:
            scored = [
                item.model_copy(
                    update={
                        "score": item.score + 1.0,
                        "breakdown": [
                            *item.breakdown,
                            ScoreContribution(
                                component="objective_fit",
                                raw_value=1.0,
                                weight=1.0,
                                contribution=1.0,
                            ),
                        ],
                    }
                )
                if domains.get(item.candidate.rule_id) is objective_tree
                else item
                for item in scored
            ]
        ranked = self._ranker.rank(scored)
        resolution = self._conflict_resolver.resolve(ranked)
        avoid_candidate_id = request.metadata.get("avoid_candidate_id")
        if isinstance(avoid_candidate_id, str) and avoid_candidate_id:
            remaining = [
                item
                for item in resolution.active
                if item.candidate.candidate_id != avoid_candidate_id
            ]
            if not remaining:
                context = context.model_copy(
                    update={
                        "uncertainty": [
                            *context.uncertainty,
                            "No different recommendation passed the current context "
                            "and safety checks.",
                        ]
                    }
                )
            resolution = resolution.model_copy(update={"active": remaining})

        trace_id = str(uuid4())
        recommendation = self._recommendation_builder.build(
            context=context,
            resolution=resolution,
            selected_trees=selected_trees,
            trace_id=trace_id,
        )
        weather = context.present.get("weather") or {}
        forecast = context.future.get("weather") or {}
        observations = [
            f"current {weather['condition']}" if weather.get("condition") else "",
            f"current rainfall class {weather['rainfall_class']}"
            if weather.get("rainfall_class")
            else "",
            f"current rainfall {weather['rainfall_mm']} mm"
            if weather.get("rainfall_mm") is not None
            else "",
            f"forecast {forecast['condition']}" if forecast.get("condition") else "",
            f"forecast rainfall {forecast['rainfall_mm']} mm"
            if forecast.get("rainfall_mm") is not None
            else "",
        ]
        observations = [item for item in observations if item]
        if observations:
            recommendation = recommendation.model_copy(
                update={
                    "reasons": [
                        *recommendation.reasons,
                        f"Weather context: {', '.join(observations)}.",
                    ]
                }
            )
        score_records = [
            CandidateScoreRecord(
                candidate_id=item.candidate.candidate_id,
                score=item.score,
                rank=item.rank or 0,
                breakdown=item.breakdown,
            )
            for item in ranked
        ]
        trace = TraceRecord(
            trace_id=trace_id,
            request_id=request.request_id,
            crop_id=request.crop_id,
            channel=request.channel,
            context_used={**context.model_dump(mode="json"), "criteria_review": criteria_review},
            relevant_history_used=context.past,
            present_conditions_used=context.present,
            future_conditions_used=context.future,
            selected_trees=selected_trees,
            evaluated_rules=evaluations,
            constraints=constraint_decisions,
            score_components=score_records,
            ranked_candidates=[item.candidate.candidate_id for item in ranked],
            conflicts=resolution.conflicts,
            final_recommendation=recommendation.recommendation_id,
            reasons=recommendation.reasons,
            warnings=recommendation.warnings,
            actions=recommendation.actions,
            started_at=started_at,
        )
        transaction = (
            self._transaction_manager.transaction()
            if self._transaction_manager is not None
            else nullcontext()
        )
        with transaction:
            self._trace_recorder.record(trace)
            self._recommendation_repository.save(recommendation)
            self._passport_service.record_decision(
                request.passport_id,
                recommendation.recommendation_id,
                trace.trace_id,
            )
            self._history_provider.append(
                request.farmer_id,
                {
                    "crop_id": request.crop_id,
                    "crop_family": context.crop_profile.family if context.crop_profile else None,
                    "event_type": "recommendation",
                    "recommendation_id": recommendation.recommendation_id,
                    "trace_id": trace.trace_id,
                    "recorded_at": trace.completed_at.isoformat(),
                },
            )
        return recommendation

    @staticmethod
    def _review_criteria(context: AgriculturalContext) -> dict[str, str]:
        """Record which T1-T7 inputs were available before ranking advice."""
        present = context.present
        future = context.future
        inputs = {
            TreeId.CROP_PROFILE: context.crop_profile is not None,
            TreeId.SOIL: bool(present.get("soil")),
            TreeId.REGION: bool(context.region or context.locality),
            TreeId.TOPOGRAPHY: bool(present.get("topography")),
            TreeId.WEATHER: bool(present.get("weather") or future.get("weather")),
            TreeId.TIMING: bool(
                present.get("current_stage") or present.get("cultivation_period") or future
            ),
            TreeId.PRACTICES_RISKS: bool(
                present.get("practices")
                or present.get("observations")
                or context.past.get("history")
                or context.past.get("passport")
            ),
        }
        return {tree.value: "available" if inputs[tree] else "missing" for tree in TreeId}

    def _evaluate_forest(
        self,
        context: AgriculturalContext,
        initial_trees: list[TreeId],
    ) -> tuple[list[Rule], list[RuleEvaluation], list[TreeId]]:
        selected_trees = list(initial_trees)
        rules_by_id: dict[str, Rule] = {}
        evaluations_by_id: dict[str, RuleEvaluation] = {}

        while True:
            retrieved = self._knowledge_provider.get_relevant_rules(
                context.crop_id, context, selected_trees
            )
            for rule in retrieved:
                if rule.rule_id not in rules_by_id:
                    rules_by_id[rule.rule_id] = rule
                    evaluations_by_id[rule.rule_id] = self._evaluator.evaluate(rule, context)

            required = [
                tree
                for rule_id, rule in rules_by_id.items()
                if evaluations_by_id[rule_id].outcome is EvaluationOutcome.MATCHED
                for tree in rule.requires_trees
            ]
            expanded = self._tree_selector.expand(selected_trees, required)
            if expanded == selected_trees:
                break
            selected_trees = expanded

        return list(rules_by_id.values()), list(evaluations_by_id.values()), selected_trees
