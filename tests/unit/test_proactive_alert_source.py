from engine.sms import CameroonRegion
from services.proactive_alert_source import KnowledgeBackedProactiveAlertSource


def test_source_returns_no_alert_without_explicit_validated_knowledge() -> None:
    assert KnowledgeBackedProactiveAlertSource(object()).list_alerts(CameroonRegion.SOUTH) == []
