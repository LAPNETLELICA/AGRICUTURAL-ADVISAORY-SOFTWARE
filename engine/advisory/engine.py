"""Crop-centered advisory pipeline orchestration."""

from __future__ import annotations

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
)
from engine.models.domain import AgriculturalContext, Rule, RuleEvaluation
from engine.models.enums import Channel, EvaluationOutcome, TreeId
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

    def advise(self, request: AdvisoryRequest) -> Recommendation:
        started_at = datetime.now(UTC)
        passport = self._passport_service.open_for_request(request)
        if passport and request.passport_id != passport.passport_id:
            request = request.model_copy(update={"passport_id": passport.passport_id})

        context = self._context_builder.build(request)
        selected_trees = self._tree_selector.select(context)
        rules, evaluations, selected_trees = self._evaluate_forest(context, selected_trees)
        del rules

        eligible, constraint_decisions, penalties = self._constraint_processor.apply(
            evaluations, context
        )
        strategy = (
            self._sms_scoring if context.channel is Channel.SMS else self._mobile_scoring
        )
        scored = strategy.score(eligible, penalties)
        ranked = self._ranker.rank(scored)
        resolution = self._conflict_resolver.resolve(ranked)

        trace_id = str(uuid4())
        recommendation = self._recommendation_builder.build(
            context=context,
            resolution=resolution,
            selected_trees=selected_trees,
            trace_id=trace_id,
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
            context_used=context.model_dump(mode="json"),
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
