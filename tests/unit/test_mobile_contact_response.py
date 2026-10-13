"""The mobile API adds support guidance without changing the engine result."""

from types import SimpleNamespace
from unittest.mock import Mock

from api.mobile import mobile_advisory
from engine.models.enums import Channel, RecommendationType
from engine.models.requests import MobileAdvisoryRequest
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.action_guidance import ActionGuidanceService
from services.auth import Principal
from services.contact_recommendation import ContactRecommendationService


def test_mobile_advisory_attaches_contact_guidance_after_engine_result() -> None:
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="tomato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="general_guidance",
            summary="Maintain regular crop monitoring.",
            score=1.0,
            rank=1,
        ),
        actions=["Apply the recommended fertilizer."],
        trace_id="trace-1",
    )
    engine = Mock()
    engine.advise.return_value = recommendation
    http_request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                media_service=Mock(),
                action_guidance_service=ActionGuidanceService(),
                contact_recommendation_service=ContactRecommendationService(),
                application_context=Mock(get=Mock(return_value=None)),
            )
        )
    )
    request = MobileAdvisoryRequest(
        request_id="request-1",
        farmer_id="farmer-1",
        crop_id="tomato",
        question="What should I do?",
    )

    result = mobile_advisory(
        request,
        http_request,
        SimpleNamespace(engine=engine),
        Principal("farmer-1", "farmer"),
    )

    assert result.primary == recommendation.primary
    assert result.actions == recommendation.actions
    assert result.contact_recommendation is not None
    assert result.contact_recommendation.vendor_category == "fertilizer"