from pathlib import Path

import pytest

from engine.bootstrap import build_container
from engine.config import Settings
from integrations.sms.tranzak import TranzakSMSProvider


class FakeResponse:
    def __init__(self, payload): self._payload = payload
    def raise_for_status(self): pass
    def json(self): return self._payload


class FakeSession:
    def __init__(self): self.calls = []
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(
            {"data": {"token": "token", "expiresIn": 3600}, "success": True}
            if url.endswith("/auth/token")
            else {"data": {"reference": "ref"}, "success": True}
        )


def test_tranzak_provider_gets_token_then_sends_sms() -> None:
    session = FakeSession()
    provider = TranzakSMSProvider("app", "key", "AGRIADVISE", session=session)
    receipt = provider.send("+237677123456", "tomato", "Test message")
    assert receipt.status.value == "delivered"
    assert session.calls[1][1]["json"]["phones"] == "+237677123456"


def test_tranzak_provider_rejects_unsuccessful_sms_response() -> None:
    class RejectedSession(FakeSession):
        def post(self, url, **kwargs):
            if url.endswith("/auth/token"):
                return super().post(url, **kwargs)
            return FakeResponse({"success": False, "errorMsg": "Sender ID is not approved"})

    provider = TranzakSMSProvider("app", "key", "AGRIADVISE", session=RejectedSession())

    with pytest.raises(ValueError, match="Sender ID is not approved"):
        provider.send("+237677123456", "tomato", "Test message")


def test_tranzak_provider_rejects_failed_per_message_status() -> None:
    class FailedStatusSession(FakeSession):
        def post(self, url, **kwargs):
            if url.endswith("/auth/token"):
                return super().post(url, **kwargs)
            return FakeResponse(
                {
                    "data": {
                        "sms": [{"phone": "+237677123456", "status": -10, "errorMsg": "rejected"}]
                    },
                    "success": True,
                }
            )

    provider = TranzakSMSProvider("app", "key", "AGRIADVISE", session=FailedStatusSession())

    with pytest.raises(ValueError, match="Tranzak rejected the SMS"):
        provider.send("+237677123456", "tomato", "Test message")


def test_container_selects_tranzak_when_provider_credentials_are_configured() -> None:
    project_root = Path(__file__).resolve().parents[2]
    container = build_container(
        Settings(
            environment="test",
            knowledge_path=project_root / "BASE_CONNAISSANCES_AGRICOLES",
            sms_provider="tranzak",
            tranzak_app_id="app-id",
            tranzak_app_key="app-key",
            tranzak_sender_id="AGRIADVISE",
        )
    )

    assert isinstance(container.sms, TranzakSMSProvider)
