from pathlib import Path

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
        return FakeResponse({"token": "token", "expiresIn": 3600} if url.endswith("/auth/token") else {"reference": "ref"})


def test_tranzak_provider_gets_token_then_sends_sms() -> None:
    session = FakeSession()
    provider = TranzakSMSProvider("app", "key", "AGRIADVISE", session=session)
    receipt = provider.send("+237677123456", "tomato", "Test message")
    assert receipt.status.value == "delivered"
    assert session.calls[1][1]["json"]["phones"] == "+237677123456"


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
