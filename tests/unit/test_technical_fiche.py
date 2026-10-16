from dataclasses import dataclass
from types import SimpleNamespace

from api.education import education_technical_fiches
from api.technical_fiches import _pdf_document
from engine.models.enums import Channel, RecommendationType
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.auth import Principal
from services.technical_fiche import TechnicalFicheService


def test_fiche_contains_nine_ordered_sections_from_real_recommendation_and_trace(container) -> None:
    request = MobileAdvisoryRequest(
        farmer_id="farmer-1",
        crop_id="tomato",
        question="How can I improve my soil?",
        objective="soil_improvement",
        region="West",
        locality="Bafoussam",
    )
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    trace = container.traces.get(recommendation.trace_id)
    assert trace is not None
    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1",
        recommendation=recommendation,
        subject="tomato soil",
        language="fr-CM",
        trace=trace,
    )

    assert [item["id"] for item in fiche.content["sections"]] == [
        "cover",
        "executive_summary",
        "farm_context",
        "diagnosis",
        "recommendations",
        "action_calendar",
        "monitoring",
        "safety",
        "references",
    ]
    assert fiche.content["recommendations"]["primary"] == recommendation.primary.name
    assert fiche.content["recommendations"]["steps"] == recommendation.actions
    assert fiche.content["farm_context"]["locality"] == "Bafoussam"
    assert fiche.content["language"]["rendered"] == "fr"
    assert fiche.content["references"]["sources"]
    assert "confidence" not in fiche.content["diagnosis"]


def test_fiche_with_missing_optional_context_does_not_invent_facts() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="Observe crop",
            summary="Inspect leaves.",
            score=1.0,
            rank=1,
        ),
        actions=["Inspect leaves."],
        trace_id="trace-1",
    )
    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="crop care", language="es"
    )
    assert "surface_area" not in fiche.content["farm_context"]
    assert "variety" not in fiche.content["farm_context"]
    assert "confidence" not in fiche.content["diagnosis"]
    assert fiche.content["language"]["rendered"] == "en"
    assert fiche.content["language"]["fallback_note"]


def test_repeated_create_reuses_owner_recommendation_fiche() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="Inspect leaves",
            summary="Inspect leaves before acting.",
            score=1.0,
            rank=1,
        ),
        trace_id="trace-1",
    )
    service = TechnicalFicheService(None)
    first = service.from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="tomato", language="en"
    )
    repeated = service.from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="tomato", language="en"
    )
    another_owner = service.from_recommendation(
        owner_id="farmer-2", recommendation=recommendation, subject="tomato", language="en"
    )
    assert first.fiche_id == repeated.fiche_id
    assert first.fiche_id != another_owner.fiche_id


def test_provider_exception_and_private_keys_never_enter_fiche() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="Inspect leaves",
            summary="Inspect leaves before acting.",
            score=1.0,
            rank=1,
        ),
        warnings=["Weather provider unavailable: TimeoutError api.openweathermap.org"],
        trace_id="trace-1",
    )
    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1",
        recommendation=recommendation,
        subject="tomato",
        language="en",
        context={"farmer_id": "farmer-private", "phone": "+237600000000"},
        weather={"error": "Traceback /app/api/weather.py", "month": 8},
    )
    visible = str(fiche.content).casefold()
    assert "provider unavailable" not in visible
    assert "api.openweathermap.org" not in visible
    assert "farmer-private" not in visible
    assert "+237600000000" not in visible
    assert "'weather': ['8']" not in visible


def test_insufficient_evidence_fiche_is_preliminary() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="insufficient-evidence",
            type=RecommendationType.ADVISORY,
            name="insufficient_evidence",
            summary="Not enough evidence for treatment.",
            score=0.0,
            rank=1,
        ),
        actions=["Provide more observations."],
        trace_id="trace-1",
    )
    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="tomato", language="en"
    )
    assert fiche.content["cover"]["validation_status"] == "preliminary"
    assert fiche.content["recommendations"]["limitations"]
    assert "confidence" not in fiche.content["diagnosis"]
    assert "application_rate" not in fiche.content["recommendations"]


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
    document = _pdf_document(
        [f"Action {index}: monitor the crop carefully." for index in range(100)]
    )

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
                technical_fiche_service=SimpleNamespace(list_visible=lambda **_: [fiche])
            )
        )
    )

    result = education_technical_fiches(request, Principal("farmer-1", "farmer"))

    assert result[0]["download_url"] == "/api/v1/technical-fiches/fiche-1/download"
