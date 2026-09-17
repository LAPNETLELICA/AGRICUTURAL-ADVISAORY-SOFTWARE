"""Education views derived strictly from the versioned T1-T7 knowledge forest."""

from __future__ import annotations

from typing import Any

from engine.models.domain import AgriculturalContext
from engine.models.enums import Channel, TreeId
from integrations.knowledge import JSONKnowledgeProvider

TREE_TITLES = {
    TreeId.CROP_PROFILE: "Crop care and crop profile",
    TreeId.SOIL: "Soil care and soil improvement",
    TreeId.REGION: "Regional suitability",
    TreeId.TOPOGRAPHY: "Topography and field positioning",
    TreeId.WEATHER: "Weather and climate",
    TreeId.TIMING: "Cultivation timing and calendar",
    TreeId.PRACTICES_RISKS: "Practices, prevention and risks",
}


class EducationService:
    def __init__(self, knowledge: JSONKnowledgeProvider) -> None:
        self._knowledge = knowledge

    def curriculum(self, crop_id: str) -> dict[str, Any]:
        profile = self._knowledge.get_crop_profile(crop_id)
        if profile is None:
            raise ValueError("crop not found")
        context = AgriculturalContext(
            request_id="education-preview",
            crop_id=crop_id,
            channel=Channel.MOBILE,
            crop_profile=profile,
        )
        modules: list[dict[str, Any]] = []
        for tree in TreeId:
            rules = self._knowledge.get_relevant_rules(crop_id, context, [tree])
            lessons = [
                {
                    "rule_id": rule.rule_id,
                    "title": rule.candidate.name,
                    "summary": rule.candidate.summary,
                    "actions": rule.candidate.actions,
                    "warnings": rule.candidate.warnings,
                    "source": rule.source.model_dump(mode="json"),
                    "status": rule.status.value,
                }
                for rule in rules
                if rule.domain is tree
            ]
            if tree is TreeId.CROP_PROFILE:
                lessons.insert(
                    0,
                    {
                        "rule_id": None,
                        "title": profile.name,
                        "summary": (
                            f"Crop family: {profile.family}. "
                            f"Cycle: {profile.cycle_length_days} days."
                        ),
                        "actions": [f"Growth stages: {', '.join(profile.growth_stages)}"]
                        if profile.growth_stages
                        else [],
                        "warnings": [],
                        "source": profile.source.model_dump(mode="json"),
                        "status": profile.status.value,
                    },
                )
            modules.append(
                {
                    "tree_id": tree.value,
                    "title": TREE_TITLES[tree],
                    "lesson_count": len(lessons),
                    "lessons": lessons,
                }
            )
        return {
            "crop_id": profile.crop_id,
            "crop_name": profile.name,
            "version": profile.version,
            "seven_criteria": modules,
            "notice": (
                "Educational content is generated from the same governed crop profile and "
                "T1-T7 rule knowledge used by the advisory engine."
            ),
        }
