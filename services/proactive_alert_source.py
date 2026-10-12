"""Safe boundary for future validated region-scoped proactive alerts.

Knowledge may later provide entries containing message, fingerprint, provenance,
validated=true and an explicit scope. Until then this source intentionally emits none.
"""

from engine.sms import CameroonRegion, ProactiveAlert


class KnowledgeBackedProactiveAlertSource:
    def __init__(self, knowledge: object) -> None:
        self._knowledge = knowledge

    def list_alerts(self, region: CameroonRegion) -> list[ProactiveAlert]:
        """Return no candidates until the validated provider exposes explicit alerts."""
        del region
        return []
