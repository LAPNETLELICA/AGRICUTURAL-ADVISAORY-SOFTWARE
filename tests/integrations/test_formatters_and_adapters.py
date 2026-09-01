import pytest

from engine.exceptions import ProviderUnavailableError
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest
from integrations.speech import DisabledSpeechProvider
from integrations.translation import PassthroughTranslator
from languages import MobileFormatter, SMSFormatter, VoiceFormatter


def _recommendation(container):
    request = MobileAdvisoryRequest(
        farmer_id="formatter-farmer",
        crop_id="irish-potato",
        question="Give me a crop summary.",
        region="West",
    )
    return container.engine.advise(AdvisoryRequest.from_mobile(request))


def test_mobile_and_voice_formatters(container):
    recommendation = _recommendation(container)
    mobile = MobileFormatter().format(recommendation)
    voice = VoiceFormatter().format(recommendation)
    assert mobile["recommendation_id"] == recommendation.recommendation_id
    assert recommendation.primary.summary in voice
    assert "Action:" in voice


def test_sms_formatter_truncates_at_configured_limit(container):
    message = SMSFormatter(max_length=70).format(_recommendation(container))
    assert len(message) <= 70
    assert message.endswith("...")


def test_translation_passthrough_and_disabled_speech():
    assert PassthroughTranslator().translate("Advice", "fr") == "Advice"
    with pytest.raises(ProviderUnavailableError, match="text-to-speech"):
        DisabledSpeechProvider().synthesize("Advice", "en")
