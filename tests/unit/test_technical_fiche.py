from dataclasses import dataclass

from engine.models.enums import Channel, RecommendationType
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from api.technical_fiches import _pdf_document
from api.education import education_technical_fiches
from services.auth import Principal
from services.technical_fiche import TechnicalFicheService
from types import SimpleNamespace


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


def test_pdf_document_paginates_long_structured_fiche_content() -> None:
    document = _pdf_document([f"Action {index}: monitor the crop carefully." for index in range(100)])

    assert document.startswith(b"%PDF-")
    assert b"page 1/3" in document
    assert b"page 3/3" in document


def test_education_lists_published_fiches_with_download_urls() -> None:
    @dataclass
    class Fiche:
        fiche_id: str
        crop_id: str
        subject: str
        status: str

    fiche = Fiche(fiche_id="fiche-1", crop_id="tomato", subject="leaf spots", status="PUBLISHED")
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                technical_fiche_service=SimpleNamespace(list_published=lambda **_: [fiche])
            )
        )
    )

    result = education_technical_fiches(request, Principal("farmer-1", "farmer"))

    assert result[0]["download_url"] == "/api/v1/technical-fiches/fiche-1/download"
