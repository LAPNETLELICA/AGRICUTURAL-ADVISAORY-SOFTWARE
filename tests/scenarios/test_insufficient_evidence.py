import pytest

from engine.bootstrap import build_container
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest


@pytest.mark.scenario
def test_unmatched_specific_rules_do_not_create_false_certainty(container):
    no_weather_container = build_container(container.settings)

    request = MobileAdvisoryRequest(
        farmer_id="cautious-farmer",
        crop_id="irish-potato",
        question="Can I plant now?",
        objective="planting",
    )

    result = no_weather_container.engine.advise(AdvisoryRequest.from_mobile(request))

    assert result.rule_references
    assert all(rule.startswith("cameroon.potato.") for rule in result.rule_references)
    assert result.primary.rule_id.startswith("cameroon.potato.")
