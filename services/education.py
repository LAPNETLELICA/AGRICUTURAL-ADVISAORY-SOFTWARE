"""Education views derived strictly from the versioned T1-T7 knowledge forest."""

from __future__ import annotations

from typing import Any

from engine.models.domain import AgriculturalContext
from engine.models.enums import Channel, TreeId
from integrations.cameroon_knowledge import CameroonKnowledgeProvider

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
    def __init__(self, knowledge: CameroonKnowledgeProvider) -> None:
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
            lessons: list[dict[str, Any]] = [
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

    def learning_curriculum(
        self,
        *,
        subject: str,
        knowledge_level: str,
        language: str,
        vocabulary_level: str,
        identity_type: str = "farmer",
    ) -> dict[str, Any]:
        """Build level-appropriate study material from the governed crop forest."""
        normalized = subject.strip().lower()
        if not normalized:
            raise ValueError("subject is required")
        if knowledge_level.lower() not in {"beginner", "basic", "intermediate", "advanced"}:
            raise ValueError("unknown knowledge level")
        professional = identity_type.lower() in {
            "professional",
            "agronomist",
            "expert",
            "extension_worker",
            "agricultural_professional",
        }
        technical = professional or knowledge_level.lower() in {"intermediate", "advanced"}
        crop = self._knowledge.get_crop_profile(normalized)
        if crop is None:
            raise ValueError("crop not found in the knowledge forest")
        forest = self.curriculum(crop.crop_id)
        tree_ids = {tree.value for tree in TreeId} if technical else {"T1", "T2", "T6", "T7"}
        modules: list[dict[str, Any]] = []
        for section in forest["seven_criteria"]:
            if section["tree_id"] not in tree_ids:
                continue
            lessons = section["lessons"]
            notes = []
            for lesson in lessons:
                if lesson["summary"]:
                    notes.append(str(lesson["summary"]))
                notes.extend(str(action) for action in lesson["actions"] if action)
                notes.extend(str(warning) for warning in lesson["warnings"] if warning)
            if not technical:
                notes = notes[:4]
            modules.append(
                {
                    "module_id": f"{crop.crop_id}-{section['tree_id'].lower()}",
                    "tree_id": section["tree_id"],
                    "title": section["title"],
                    "lesson_count": len(lessons),
                    "learning_outcome": f"Apply {section['title'].lower()} to {crop.name}.",
                    "notes": notes,
                    "lessons": lessons,
                    "source": lessons[0]["source"]
                    if lessons
                    else crop.source.model_dump(mode="json"),
                }
            )
        return {
            "subject": crop.crop_id,
            "knowledge_level": knowledge_level.lower(),
            "language": language,
            "vocabulary_level": vocabulary_level.lower(),
            "modules": modules,
            "content_policy": "Adapted presentation; agricultural facts remain unchanged.",
        }
