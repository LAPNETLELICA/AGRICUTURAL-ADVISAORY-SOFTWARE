"""Explicit conflict resolution with an auditable winner decision."""

from __future__ import annotations

from collections import defaultdict

from engine.models.domain import (
    ConflictRecord,
    ConflictResolution,
    ScoredCandidate,
)


class ConflictResolver:
    def resolve(self, ranked: list[ScoredCandidate]) -> ConflictResolution:
        grouped: dict[str, list[ScoredCandidate]] = defaultdict(list)
        active: list[ScoredCandidate] = []

        for item in ranked:
            group = item.candidate.conflict_group
            if group:
                grouped[group].append(item)
            else:
                active.append(item)

        conflicts: list[ConflictRecord] = []
        suppressed: list[ScoredCandidate] = []
        for group, items in grouped.items():
            winner, *losers = items
            active.append(winner)
            if losers:
                suppressed.extend(losers)
                conflicts.append(
                    ConflictRecord(
                        conflict_group=group,
                        selected_candidate_id=winner.candidate.candidate_id,
                        rejected_candidate_ids=[item.candidate.candidate_id for item in losers],
                        reason=(
                            "Selected by ranked score, then validated rule priority, "
                            "then stable candidate identifier."
                        ),
                        selected_rule_priority=winner.candidate.rule_priority,
                        rejected_rule_priorities={
                            item.candidate.candidate_id: item.candidate.rule_priority
                            for item in losers
                        },
                    )
                )

        active.sort(key=lambda item: item.rank or 0)
        suppressed.sort(key=lambda item: item.rank or 0)
        return ConflictResolution(active=active, suppressed=suppressed, conflicts=conflicts)

