from engine.models.enums import Channel, RecommendationType
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.contact_recommendation import ContactRecommendationService


def _recommendation(
    name: str = "general_guidance",
    actions: list[str] | None = None,
    warnings: list[str] | None = None,
) -> Recommendation:
    return Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name=name,
            summary="Maintain crop monitoring.",
            score=1.0,
            rank=1,
        ),
        actions=actions or [],
        warnings=warnings or [],
        trace_id="trace-1",
    )


def test_fertilizer_action_requires_fertilizer_vendor() -> None:
    result = ContactRecommendationService().evaluate(
        _recommendation(actions=["Apply fertilizer."]), []
    )
    assert result.vendor_required is True
    assert result.vendor_category == "fertilizer"


def test_insufficient_evidence_requires_field_assessment() -> None:
    result = ContactRecommendationService().evaluate(
        _recommendation(name="insufficient_evidence"), []
    )
    assert result.specialist_required is True
    assert result.specialist_category == "field_assessment"


def test_disease_treatment_requires_specialist_and_vendor() -> None:
    result = ContactRecommendationService().evaluate(
        _recommendation(
            actions=["Obtain treatment."],
            warnings=["Suspected disease requires field confirmation."],
        ),
        [],
    )
    assert result.specialist_category == "crop_disease"
    assert result.vendor_category == "agricultural_treatment"
