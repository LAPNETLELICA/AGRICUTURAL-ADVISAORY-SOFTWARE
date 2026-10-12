import pytest

from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest


def test_repositories_return_defensive_copies(container):
    request = MobileAdvisoryRequest(
        farmer_id="copy-farmer",
        crop_id="irish-potato",
        question="Create records.",
    )
    result = container.engine.advise(AdvisoryRequest.from_mobile(request))
    stored = container.recommendations.get(result.recommendation_id)
    assert stored is not None
    stored.actions.append("local mutation")
    assert "local mutation" not in container.recommendations.get(result.recommendation_id).actions

    trace = container.traces.get(result.trace_id)
    assert trace is not None
    trace.warnings.append("local mutation")
    assert "local mutation" not in container.traces.get(result.trace_id).warnings


def test_unknown_or_wrong_owner_passport_is_rejected(container):
    missing = MobileAdvisoryRequest(
        farmer_id="passport-owner",
        crop_id="irish-potato",
        passport_id="missing-passport",
        question="Continue.",
    )
    with pytest.raises(ValueError, match="not found"):
        container.engine.advise(AdvisoryRequest.from_mobile(missing))

    first = MobileAdvisoryRequest(
        farmer_id="passport-owner",
        crop_id="irish-potato",
        plot_ref="secure-plot",
        question="Open passport.",
    )
    container.engine.advise(AdvisoryRequest.from_mobile(first))
    passport = container.passports.find("passport-owner", "irish-potato", "secure-plot")
    assert passport is not None
    wrong_owner = MobileAdvisoryRequest(
        farmer_id="different-farmer",
        crop_id="irish-potato",
        passport_id=passport.passport_id,
        question="Try another passport.",
    )
    with pytest.raises(ValueError, match="does not belong"):
        container.engine.advise(AdvisoryRequest.from_mobile(wrong_owner))
