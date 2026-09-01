import pytest

from engine.models.enums import TreeId
from engine.models.requests import (
    AdvisoryRequest,
    EvidenceInput,
    MobileAdvisoryRequest,
    SMSAdvisoryRequest,
)


@pytest.mark.scenario
def test_book_scenario_produces_multi_tree_traceable_advice(container):
    request = MobileAdvisoryRequest(
        farmer_id="scenario-farmer",
        crop_id="irish-potato",
        question="How should I improve yield and prepare this plot?",
        objective="yield_improvement",
        region="West",
        locality="Bafoussam",
        current_stage="pre-planting",
        evidence=EvidenceInput(
            soil={"drainage": "poor"},
            topography={"landform": "flatland"},
            weather={"rainfall_class": "heavy", "consecutive_rain_days": 3},
            future={"month": 8},
        ),
    )
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))

    assert recommendation.primary.name == "late_blight_watch"
    assert {item.type.value for item in recommendation.alternatives} >= {
        "soil_action",
        "timing",
    }
    assert recommendation.selected_trees == list(TreeId)
    assert len(recommendation.actions) >= 3
    assert recommendation.trace_id

    trace = container.traces.get(recommendation.trace_id)
    assert trace is not None
    assert trace.crop_id == "irish-potato"
    assert trace.relevant_history_used is not None
    assert trace.present_conditions_used["weather"]["rainfall_class"] == "heavy"
    assert trace.future_conditions_used["month"] == 8
    assert len(trace.evaluated_rules) == 5
    assert trace.ranked_candidates[0] == "demo.potato.late-blight-watch"
    assert trace.final_recommendation == recommendation.recommendation_id


@pytest.mark.scenario
def test_mobile_and_sms_share_rules_but_apply_different_scores(container):
    evidence = EvidenceInput(
        weather={"rainfall_class": "heavy", "consecutive_rain_days": 3},
        future={"month": 8},
    )
    mobile = MobileAdvisoryRequest(
        farmer_id="channel-farmer",
        crop_id="irish-potato",
        question="What is the current risk?",
        objective="risk",
        region="West",
        evidence=evidence,
    )
    sms = SMSAdvisoryRequest(
        recipient_id="channel-phone",
        crop_id="irish-potato",
        farmer_id="channel-farmer",
        region="West",
        cultivation_period="August",
        evidence=evidence,
    )
    mobile_result = container.engine.advise(AdvisoryRequest.from_mobile(mobile))
    sms_result = container.engine.advise(AdvisoryRequest.from_sms(sms))

    assert mobile_result.primary.rule_id == sms_result.primary.rule_id
    assert mobile_result.primary.score == 5.0
    assert sms_result.primary.score == 9.0
    assert mobile_result.channel.value == "mobile"
    assert sms_result.channel.value == "sms"


@pytest.mark.scenario
def test_crop_passport_is_reused_and_accumulates_decisions(container):
    first = MobileAdvisoryRequest(
        farmer_id="passport-farmer",
        crop_id="irish-potato",
        plot_ref="plot-a",
        current_stage="planting",
        question="Start this crop passport.",
        region="West",
    )
    first_result = container.engine.advise(AdvisoryRequest.from_mobile(first))
    passport = container.passports.find("passport-farmer", "irish-potato", "plot-a")
    assert passport is not None
    assert first_result.recommendation_id in passport.recommendation_ids

    second = MobileAdvisoryRequest(
        farmer_id="passport-farmer",
        crop_id="irish-potato",
        passport_id=passport.passport_id,
        plot_ref="plot-a",
        current_stage="vegetative",
        question="Continue guidance for this crop.",
        region="West",
    )
    second_result = container.engine.advise(AdvisoryRequest.from_mobile(second))
    updated = container.passports.get(passport.passport_id)
    assert updated is not None
    assert updated.current_stage == "vegetative"
    assert second_result.recommendation_id in updated.recommendation_ids
    assert len(updated.recommendation_ids) == 2
