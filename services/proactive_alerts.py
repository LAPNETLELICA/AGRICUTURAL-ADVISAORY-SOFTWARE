"""One safe cycle for future region-scoped proactive SMS delivery."""

from dataclasses import dataclass

from engine.sms import CameroonRegion


@dataclass(frozen=True, slots=True)
class ProactiveRunSummary:
    sent: int = 0
    failed: int = 0
    skipped: int = 0


class ProactiveAlertService:
    def __init__(self, source: object, repository: object | None = None, gateway: object | None = None, *, enabled: bool = False) -> None:
        self._source = source
        self._repository = repository
        self._gateway = gateway
        self._enabled = enabled

    def run_once(self) -> ProactiveRunSummary:
        """Remain idle until a validated source and delivery routing are configured."""
        if not self._enabled:
            return ProactiveRunSummary(skipped=1)
        if self._repository is None or self._gateway is None:
            return ProactiveRunSummary(skipped=1)
        sent = failed = skipped = 0
        for region in CameroonRegion:
            for alert in self._source.list_alerts(region):
                if not alert.validated or alert.scope.region != region:
                    skipped += 1
                    continue
                for registration in self._repository.resolve_active_recipients(alert.scope):
                    if self._repository.was_alert_delivered(registration.registration_id, alert.fingerprint):
                        skipped += 1
                        continue
                    state = "sent"
                    try:
                        self._gateway.send(registration.phone, "regional-alert", alert.message)
                        sent += 1
                    except Exception:
                        state = "failed"; failed += 1
                    self._repository.create_delivery(registration_id=registration.registration_id, scope=alert.scope, source="automatic", message=alert.message, status=state, alert_fingerprint=alert.fingerprint)
        return ProactiveRunSummary(sent=sent, failed=failed, skipped=skipped)
