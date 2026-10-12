from services.proactive_alerts import ProactiveAlertService
from engine.sms import CameroonRegion, DeliveryScope, ProactiveAlert, SMSRegistration


def test_disabled_proactive_worker_does_not_send() -> None:
    assert ProactiveAlertService(object(), enabled=False).run_once().sent == 0


def test_worker_sends_valid_south_alert_only_to_south_registration() -> None:
    class Source:
        def list_alerts(self, region):
            return [ProactiveAlert("Alert", DeliveryScope.region_scope("South"), "south-1", "knowledge", True)] if region is CameroonRegion.SOUTH else []
    class Repository:
        def resolve_active_recipients(self, scope): return [SMSRegistration("s", "+237677123456", CameroonRegion.SOUTH)]
        def was_alert_delivered(self, *_): return False
        def create_delivery(self, **_): return "d"
    class Gateway:
        def __init__(self): self.phones = []
        def send(self, phone, *_): self.phones.append(phone)
    gateway = Gateway()
    assert ProactiveAlertService(Source(), Repository(), gateway, enabled=True).run_once().sent == 1
    assert gateway.phones == ["+237677123456"]
