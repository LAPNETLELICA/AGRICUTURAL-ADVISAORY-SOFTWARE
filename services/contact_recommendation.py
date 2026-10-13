"""Determine whether an existing recommendation calls for external support."""

from engine.models.responses import ContactRecommendation, Recommendation


class ContactRecommendationService:
    def evaluate(
        self, recommendation: Recommendation, visual_evidence: list[dict[str, object]]
    ) -> ContactRecommendation:
        text = " ".join(
            [
                recommendation.primary.name,
                recommendation.primary.summary,
                *recommendation.actions,
                *recommendation.warnings,
            ]
        ).casefold()
        specialist = recommendation.primary.name == "insufficient_evidence" or any(
            not item.get("relevant", True) for item in visual_evidence
        )
        disease = any(
            term in text
            for term in ("suspected disease", "disease confirmation", "field confirmation")
        )
        vendor = next(
            (
                category
                for term, category in (
                    ("fertilizer", "fertilizer"),
                    ("engrais", "fertilizer"),
                    ("manure", "soil_amendment"),
                    ("fumier", "soil_amendment"),
                    ("seed", "seed"),
                    ("semence", "seed"),
                    ("treatment", "agricultural_treatment"),
                )
                if term in text
            ),
            None,
        )
        return ContactRecommendation(
            specialist_required=specialist or disease,
            vendor_required=vendor is not None,
            specialist_category="crop_disease"
            if disease
            else ("field_assessment" if specialist else None),
            vendor_category=vendor,
            specialist_reason="Field assessment is advised."
            if specialist
            else ("Disease confirmation is advised." if disease else None),
            vendor_reason="The recommendation requires an agricultural input or service."
            if vendor
            else None,
        )
