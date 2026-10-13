"""Level-aware presentation metadata, independent of agricultural reasoning."""

from __future__ import annotations

from engine.models.responses import Recommendation
from services.application_context import ApplicationProfile


def adapt_recommendation(
    recommendation: Recommendation, profile: ApplicationProfile | None
) -> Recommendation:
    if profile is None:
        return recommendation
    depth = {
        "beginner": "concise",
        "basic": "practical",
        "intermediate": "detailed",
        "advanced": "technical",
    }
    return recommendation.model_copy(
        update={
            "presentation": {
                "language": profile.language,
                "vocabulary_level": profile.vocabulary_level,
                "explanation_depth": depth[profile.knowledge_level.lower()],
                "agricultural_conclusion_changed": False,
            }
        }
    )
