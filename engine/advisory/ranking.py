"""Deterministic candidate ranking."""

from engine.models.domain import ScoredCandidate


class Ranker:
    def rank(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        ordered = sorted(
            candidates,
            key=lambda item: (
                -item.score,
                -item.candidate.rule_priority,
                item.candidate.candidate_id,
            ),
        )
        return [item.model_copy(update={"rank": index}) for index, item in enumerate(ordered, 1)]

