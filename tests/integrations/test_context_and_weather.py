from pathlib import Path

from engine.bootstrap import build_container
from engine.config import Settings
from engine.models.requests import (
    AdvisoryRequest,
    EvidenceInput,
    MobileAdvisoryRequest,
)


def test_weather_failure_is_explicit_and_farmer_evidence_is_preserved():
    root = Path(__file__).resolve().parents[2]
    container = build_container(
        Settings(environment="test", knowledge_path=root / "knowledge")
    )
    request = MobileAdvisoryRequest(
        farmer_id="farmer-weather",
        crop_id="irish-potato",
        question="What should I do?",
        region="West",
        evidence=EvidenceInput(weather={"rainfall_class": "heavy"}, future={"month": 8}),
    )
    result = container.engine.advise(AdvisoryRequest.from_mobile(request))
    assert any("Weather provider unavailable" in warning for warning in result.warnings)
    trace = container.traces.get(result.trace_id)
    assert trace is not None
    assert trace.present_conditions_used["weather"]["rainfall_class"] == "heavy"


def test_irrelevant_request_history_is_not_injected(container):
    request = MobileAdvisoryRequest(
        farmer_id="farmer-history",
        crop_id="irish-potato",
        question="Review my crop.",
        region="West",
        history=[
            {"crop_id": "irish-potato", "event_type": "planting"},
            {"crop_id": "coffee", "event_type": "harvest"},
        ],
    )
    result = container.engine.advise(AdvisoryRequest.from_mobile(request))
    trace = container.traces.get(result.trace_id)
    assert trace is not None
    assert [item["crop_id"] for item in trace.relevant_history_used["history"]] == [
        "irish-potato"
    ]
