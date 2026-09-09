"""Configurable MobileScore and SMSPriority implementations."""

from __future__ import annotations

from collections.abc import Mapping

from engine.models.domain import RuleEvaluation, ScoreContribution, ScoredCandidate
from engine.models.enums import Channel


MOBILE_COMPONENTS = frozenset(
    {
        "crop_fit",
        "soil_fit",
        "soil_improvement_potential",
        "topography_fit",
        "weather_fit",
        "regional_risk_fit",
        "timing_fit",
        "practice_fit",
        "relevant_history_fit",
        "risk_penalties",
    }
)

SMS_COMPONENTS = frozenset(
    {
        "weather_change_urgency",
        "cultivation_period_relevance",
        "regional_risk",
        "soil_crop_relevance",
        "practice_relevance",
        "future_risk",
        "risk_penalties",
    }
)


class BaseScoringStrategy:
    channel: Channel
    allowed_components: frozenset[str]

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        self._weights = dict(weights or {})

    def score(
        self,
        evaluations: list[RuleEvaluation],
        penalties: dict[str, float],
    ) -> list[ScoredCandidate]:
        scored: list[ScoredCandidate] = []
        for evaluation in evaluations:
            candidate = evaluation.candidate
            if candidate is None:
                continue
            breakdown: list[ScoreContribution] = []
            total = 0.0
            for component, raw_value in sorted(candidate.score_components.items()):
                if component not in self.allowed_components:
                    continue
                weight = self._weights.get(component, 1.0)
                contribution = raw_value * weight
                if component == "risk_penalties":
                    contribution = -abs(contribution)
                total += contribution
                breakdown.append(
                    ScoreContribution(
                        component=component,
                        raw_value=raw_value,
                        weight=weight,
                        contribution=round(contribution, 6),
                    )
                )
            constraint_penalty = penalties.get(candidate.candidate_id, 0.0)
            total -= constraint_penalty
            scored.append(
                ScoredCandidate(
                    candidate=candidate,
                    score=round(total, 6),
                    breakdown=breakdown,
                    constraint_penalty=constraint_penalty,
                )
            )
        return scored


class MobileScoringStrategy(BaseScoringStrategy):
    channel = Channel.MOBILE
    allowed_components = MOBILE_COMPONENTS


class SMSPriorityScoringStrategy(BaseScoringStrategy):
    channel = Channel.SMS
    allowed_components = SMS_COMPONENTS

