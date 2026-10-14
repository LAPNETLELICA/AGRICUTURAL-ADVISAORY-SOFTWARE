from engine.models.enums import Channel, RecommendationType
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.technical_fiche import TechnicalFicheService


def test_problem_fiche_contains_contextual_diagnosis_protection_calendar_and_safety() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="Tomato leaf spot management",
            summary="Protect the crop from leaf spot disease.",
            score=1.0,
            rank=1,
        ),
        actions=["Remove affected leaves.", "Apply an approved biocontrol treatment."],
        warnings=["Do not apply treatment before heavy rain."],
        trace_id="trace-1",
    )

    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1",
        recommendation=recommendation,
        subject="leaf spots",
        language="fr",
        context={"intent": "crop_problem", "symptoms": "yellow spots", "farmer_id": "farmer-1"},
        weather={"warning": "Heavy rain expected"},
    )

    assert "general_information" in fiche.content
    assert fiche.content["diagnosis"]["observations"] == "yellow spots"
    assert "crop_protection" in fiche.content["recommendations"]
    assert fiche.content["action_calendar"][0]["status"] == "À planifier"
    assert "Heavy rain expected" in fiche.content["safety"]["weather"]
    assert "farmer_id" not in str(fiche.content)
