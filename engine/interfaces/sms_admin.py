"""Ports used by SMS administration and proactive delivery."""

from typing import Protocol

from engine.sms.models import DeliveryScope, ProactiveAlert, SMSRegistration


class SMSAdminRepository(Protocol):
    def resolve_active_recipients(self, scope: DeliveryScope) -> list[SMSRegistration]: ...


class SMSDeliveryGateway(Protocol):
    def send(self, phone: str, message: str) -> object: ...


class ProactiveAlertSource(Protocol):
    def list_alerts(self, region: object) -> list[ProactiveAlert]: ...
