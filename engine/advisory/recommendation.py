"""Build one canonical recommendation for all delivery channels."""

from __future__ import annotations

from collections.abc import Iterable

from engine.models.domain import (
    AgriculturalContext,
    ConflictResolution,
    ScoredCandidate,
)
from engine.models.enums import RecommendationType, RuleStatus, TreeId
from engine.models.responses import (
    CandidateScoreRecord,
    CanonicalRecommendationItem,
    Recommendation,
)


def _unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


class RecommendationBuilder:
    def build(
        self,
        *,
        context: AgriculturalContext,
        resolution: ConflictResolution,
        selected_trees: list[TreeId],
        trace_id: str,
    ) -> Recommendation:
        if not resolution.active:
            primary = CanonicalRecommendationItem(
                candidate_id="insufficient-evidence",
                type=RecommendationType.ADVISORY,
                name="insufficient_evidence",
                summary=(
                    "There is not enough validated crop-specific evidence for a reliable action."
                ),
                score=0.0,
                rank=1,
                rule_id=None,
            )
            warnings = [
                "Insufficient validated evidence; no agricultural threshold was inferred "
                "by the engine."
            ]
            actions = [
                "Provide more crop-specific observations or ask a qualified agronomy expert."
            ]
            reasons: list[str] = []
            alternatives: list[CanonicalRecommendationItem] = []
            rule_references: list[str] = []
            score_breakdown: list[CandidateScoreRecord] = []
        else:
            primary = self._item(resolution.active[0])
            alternatives = [self._item(item) for item in resolution.active[1:]]
            reasons = _unique(
                reason
                for item in resolution.active
                for reason in item.candidate.reasons
            )
            warnings = _unique(
                warning
                for item in resolution.active
                for warning in item.candidate.warnings
            )
            actions = _unique(
                action
                for item in resolution.active
                for action in item.candidate.actions
            )
            rule_references = _unique(item.candidate.rule_id for item in resolution.active)
            score_breakdown = [
                CandidateScoreRecord(
                    candidate_id=item.candidate.candidate_id,
                    score=item.score,
                    rank=item.rank or 0,
                    breakdown=item.breakdown,
                )
                for item in resolution.active
            ]
            if any(
                item.candidate.rule_status is not RuleStatus.VALIDATED
                for item in resolution.active
            ):
                warnings.append(
                    "Development knowledge was used; Developer 2 agronomic validation is required."
                )

        warnings = _unique([*warnings, *context.uncertainty])
        return Recommendation(
            request_id=context.request_id,
            crop_id=context.crop_id,
            channel=context.channel,
            primary=primary,
            alternatives=alternatives,
            reasons=reasons,
            warnings=warnings,
            actions=actions,
            selected_trees=selected_trees,
            rule_references=rule_references,
            score_breakdown=score_breakdown,
            trace_id=trace_id,
            uncertainty=context.uncertainty,
        )

    @staticmethod
    def _item(item: ScoredCandidate) -> CanonicalRecommendationItem:
        candidate = item.candidate
        return CanonicalRecommendationItem(
            candidate_id=candidate.candidate_id,
            type=candidate.type,
            name=candidate.name,
            summary=candidate.summary,
            score=item.score,
            rank=item.rank or 0,
            rule_id=candidate.rule_id,
        )
