from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from engine.config import Settings


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        environment="development",
        knowledge_path=Path("knowledge"),
        auth_required=True,
        auth_secret="test-secret-that-is-long-enough",
        auth_store_path=tmp_path / "users.json",
        admin_password="change-me-now",
    )
    return TestClient(create_app(settings))


def _admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "change-me-now"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_dashboard_api_and_education(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _admin_headers(client)
    assert client.get("/api/v1/admin/overview", headers=headers).status_code == 200
    education = client.get("/api/v1/education/crops/tomato", headers=headers)
    assert education.status_code == 200
    assert len(education.json()["seven_criteria"]) == 7


def test_notification_sandbox_generates_engine_message(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _admin_headers(client)
    subscription = {
        "recipient_id": "farmer-1",
        "farmer_id": "farmer-1",
        "crop_id": "tomato",
        "region": "Bafoussam",
        "language": "en",
        "enabled": True,
    }
    assert (
        client.post(
            "/api/v1/notifications/subscriptions", json=subscription, headers=headers
        ).status_code
        == 200
    )
    generated = client.post("/api/v1/notifications/trigger/farmer-1", headers=headers)
    assert generated.status_code == 200
    assert generated.json()["message"]
    inbox = client.get("/api/v1/sms/inbox/farmer-1", headers=headers)
    assert inbox.status_code == 200
    assert len(inbox.json()) == 1


def test_sensitive_endpoint_requires_token(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.get("/api/v1/admin/overview").status_code == 401
