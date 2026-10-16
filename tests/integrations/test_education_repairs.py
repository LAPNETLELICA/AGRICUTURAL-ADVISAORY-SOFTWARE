from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.app import create_app
from api.education import education_technical_fiches
from api.mobile import mobile_advisory
from api.technical_fiches import FicheCreate, create_fiche, download_fiche
from engine.advisory.context import CropContextBuilder
from engine.exceptions import ProviderUnavailableError
from engine.models.requests import AdvisoryRequest, EvidenceInput, MobileAdvisoryRequest
from services.auth import Principal
from services.education import EducationService
from services.technical_fiche import TechnicalFicheService


def test_owner_can_list_and_download_newly_generated_draft(container) -> None:
    request = MobileAdvisoryRequest(
        farmer_id="farmer-1",
        crop_id="tomato",
        question="How should I care for this crop?",
        region="West",
        locality="Bafoussam",
    )
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    app = create_app(container.settings, container)
    http_request = SimpleNamespace(app=app)
    principal = Principal("farmer-1", "farmer")
    created = create_fiche(
        FicheCreate(recommendation_id=recommendation.recommendation_id, subject="tomato care"),
        http_request,
        principal,
    )
    fiche_id = created["fiche_id"]
    assert created["status"] == "DRAFT"
    listed = education_technical_fiches(http_request, principal)
    assert any(item["fiche_id"] == fiche_id for item in listed)
    downloaded = download_fiche(fiche_id, http_request, principal)
    assert downloaded.media_type == "application/pdf"
    assert downloaded.body.startswith(b"%PDF-")
    assert b"General Information" in downloaded.body
    assert b"general_information: {" not in downloaded.body


def test_draft_visibility_is_limited_to_owner(container) -> None:
    service = TechnicalFicheService(None)
    request = MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Advice?")
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    fiche = service.from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="tomato", language="en"
    )
    assert fiche in service.list_visible(owner_id="farmer-1")
    assert fiche not in service.list_visible(owner_id="farmer-2")


def test_profile_curricula_contain_distinct_forest_based_study_notes(container) -> None:
    service = EducationService(container.knowledge)
    farmer = service.learning_curriculum(
        subject="tomato",
        identity_type="rural_farmer",
        knowledge_level="beginner",
        language="en",
        vocabulary_level="simple",
    )
    professional = service.learning_curriculum(
        subject="tomato",
        identity_type="professional",
        knowledge_level="advanced",
        language="en",
        vocabulary_level="technical",
    )
    assert farmer["modules"] != professional["modules"]
    assert all(module["notes"] for module in farmer["modules"])
    assert all(module["source"] for module in professional["modules"])
    assert {module["tree_id"] for module in professional["modules"]} == {
        "T1",
        "T2",
        "T3",
        "T4",
        "T5",
        "T6",
        "T7",
    }


def test_follow_up_recommendation_uses_another_valid_candidate(container) -> None:
    first = container.engine.advise(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(
                farmer_id="farmer-1",
                crop_id="tomato",
                question="What should I do?",
                region="West",
                locality="Bafoussam",
            )
        )
    )
    assert first.alternatives
    app = create_app(container.settings, container)
    response = mobile_advisory(
        MobileAdvisoryRequest(
            farmer_id="farmer-1",
            crop_id="tomato",
            question="What else can I do?",
            region="West",
            locality="Bafoussam",
            metadata={"previous_recommendation_id": first.recommendation_id},
        ),
        SimpleNamespace(app=app),
        container,
        Principal("farmer-1", "farmer"),
    )
    assert response.primary.candidate_id != first.primary.candidate_id
    assert response.primary.candidate_id in {item.candidate_id for item in first.alternatives}


def test_every_recommendation_records_all_seven_criteria(container) -> None:
    recommendation = container.engine.advise(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Advice?")
        )
    )
    trace = container.traces.get(recommendation.trace_id)
    assert trace is not None
    assert set(trace.context_used["criteria_review"]) == {"T1", "T2", "T3", "T4", "T5", "T6", "T7"}
    assert trace.context_used["criteria_review"]["T5"] == "available"


def test_forecast_is_fetched_even_when_current_weather_fails(container) -> None:
    class PartialWeather:
        def get_current(self, region, locality, crop_id):
            raise ProviderUnavailableError("current conditions unavailable")

        def get_forecast(self, region, locality, crop_id):
            return {"condition": "rain", "rainfall_mm": 4.0}

    builder = CropContextBuilder(
        crop_provider=container.knowledge,
        history_provider=container.history,
        weather_provider=PartialWeather(),
        passport_repository=container.passports,
    )
    context = builder.build(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Advice?")
        )
    )
    assert context.future["weather"]["condition"] == "rain"
    assert any("Current weather" in message for message in context.uncertainty)


def test_soil_objective_prioritizes_soil_rule_and_reports_weather(container) -> None:
    recommendation = container.engine.advise(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(
                farmer_id="farmer-1",
                crop_id="tomato",
                question="How can I improve my soil?",
                objective="soil_improvement",
                region="West",
                locality="Bafoussam",
            )
        )
    )
    assert recommendation.primary.rule_id == "cameroon.tomato.t2"
    assert any("weather" in reason.lower() for reason in recommendation.reasons)


def test_live_weather_values_take_precedence_over_stale_supplied_values(container) -> None:
    recommendation = container.engine.advise(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(
                farmer_id="farmer-1",
                crop_id="tomato",
                question="Advice?",
                evidence=EvidenceInput(
                    weather={"rainfall_class": "dry"},
                    future={"weather": {"month": 1}},
                ),
            )
        )
    )
    trace = container.traces.get(recommendation.trace_id)
    assert trace is not None
    assert trace.present_conditions_used["weather"]["rainfall_class"] == "heavy"
    assert trace.future_conditions_used["weather"]["month"] == 8


def test_follow_up_rejects_another_farmers_recommendation(container) -> None:
    first = container.engine.advise(
        AdvisoryRequest.from_mobile(
            MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Advice?")
        )
    )
    app = create_app(container.settings, container)
    with pytest.raises(HTTPException) as denied:
        mobile_advisory(
            MobileAdvisoryRequest(
                farmer_id="farmer-2",
                crop_id="tomato",
                question="Other advice?",
                metadata={"previous_recommendation_id": first.recommendation_id},
            ),
            SimpleNamespace(app=app),
            container,
            Principal("farmer-2", "farmer"),
        )
    assert denied.value.status_code == 403


def test_technical_fiche_omits_internal_weather_provider_errors(container) -> None:
    request = MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Advice?")
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    recommendation = recommendation.model_copy(
        update={"warnings": [*recommendation.warnings, "Weather provider unavailable: timeout"]}
    )
    fiche = TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1", recommendation=recommendation, subject="tomato", language="en"
    )
    assert "provider unavailable" not in str(fiche.content).lower()
