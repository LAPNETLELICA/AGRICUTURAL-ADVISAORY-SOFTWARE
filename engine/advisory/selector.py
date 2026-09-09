"""Crop-rooted dynamic knowledge-tree selection."""

from __future__ import annotations

from engine.models.domain import AgriculturalContext
from engine.models.enums import Channel, Objective, TreeId


TREE_ORDER = list(TreeId)


class CropTreeSelector:
    """Always start at T1 and add contextually relevant trees."""

    def select(self, context: AgriculturalContext) -> list[TreeId]:
        selected: set[TreeId] = {TreeId.CROP_PROFILE}
        present = context.present
        future = context.future
        objective = present.get("objective")

        if present.get("soil"):
            selected.add(TreeId.SOIL)
        if context.region or context.locality:
            selected.add(TreeId.REGION)
        if present.get("topography"):
            selected.add(TreeId.TOPOGRAPHY)
        if present.get("weather") or future.get("weather") or self._weather_uncertain(context):
            selected.add(TreeId.WEATHER)
        if future or present.get("cultivation_period") or objective == Objective.PLANTING:
            selected.add(TreeId.TIMING)

        practice_objectives = {
            Objective.YIELD_IMPROVEMENT,
            Objective.RISK,
            Objective.EDUCATION,
        }
        if (
            context.past
            or present.get("practices")
            or present.get("observations")
            or objective in practice_objectives
        ):
            selected.add(TreeId.PRACTICES_RISKS)

        if context.channel is Channel.SMS:
            selected.update(
                {
                    TreeId.REGION,
                    TreeId.WEATHER,
                    TreeId.TIMING,
                    TreeId.PRACTICES_RISKS,
                }
            )
        return [tree for tree in TREE_ORDER if tree in selected]

    def expand(self, selected: list[TreeId], required: list[TreeId]) -> list[TreeId]:
        expanded = set(selected)
        expanded.add(TreeId.CROP_PROFILE)
        expanded.update(required)
        return [tree for tree in TREE_ORDER if tree in expanded]

    @staticmethod
    def _weather_uncertain(context: AgriculturalContext) -> bool:
        return any("weather" in item.lower() for item in context.uncertainty)

