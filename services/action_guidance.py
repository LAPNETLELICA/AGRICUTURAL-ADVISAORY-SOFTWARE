"""Structure only agricultural actions already backed by recommendation rules."""

from engine.models.responses import ActionGuidance, Recommendation


class ActionGuidanceService:
    def resolve(self, recommendation: Recommendation) -> list[ActionGuidance]:
        if not recommendation.rule_references:
            return []
        materials = [
            action
            for action in recommendation.actions
            if any(
                term in action.casefold()
                for term in (
                    "compost",
                    "manure",
                    "fumier",
                    "fiente",
                    "engrais",
                    "seed",
                    "semence",
                    "chaux",
                )
            )
        ]
        return [
            ActionGuidance(
                action=action,
                title=recommendation.primary.name,
                recommended_materials=materials,
                application_steps=[action],
                safety_notes=recommendation.warnings,
            )
            for action in recommendation.actions
        ]
