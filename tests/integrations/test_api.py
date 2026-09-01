import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from tests.conftest import full_mobile_payload


@pytest.fixture
def client(container):
    return TestClient(create_app(container.settings, container))


def test_health_and_crop_catalogue(client):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["knowledge_loaded"] is True
    crops = client.get("/api/v1/crops")
    assert crops.status_code == 200
    assert crops.json()[0]["crop_id"] == "irish-potato"
    crop = client.get("/api/v1/crops/irish-potato")
    assert crop.status_code == 200
    assert crop.json()["family"] == "Solanaceae"
    version = client.get("/api/v1/knowledge/version")
    assert version.status_code == 200
    assert version.json()["knowledge_version"] == "0.1.0-demo"
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["docs"] == "/docs"


def test_mobile_advisory_and_trace_retrieval(client):
    response = client.post("/api/v1/advisory/mobile", json=full_mobile_payload())
    assert response.status_code == 200, response.text
    recommendation = response.json()
    assert recommendation["primary"]["name"] == "late_blight_watch"
    detail = client.get(f"/api/v1/recommendations/{recommendation['recommendation_id']}")
    assert detail.status_code == 200
    assert detail.json()["trace"]["trace_id"] == recommendation["trace_id"]


def test_sms_advisory_is_delivered_to_simulator(client):
    payload = {
        "recipient_id": "virtual-phone-1",
        "crop_id": "irish-potato",
        "region": "West",
        "cultivation_period": "August",
        "evidence": {
            "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
            "future": {"month": 8},
        },
    }
    response = client.post("/api/v1/advisory/sms", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["message"]) <= 160
    assert body["delivery"]["status"] == "delivered"
    inbox = client.get("/api/v1/sms/inbox/virtual-phone-1")
    assert inbox.json()[0]["delivery_id"] == body["delivery"]["delivery_id"]


def test_manual_sms_simulation(client):
    response = client.post(
        "/api/v1/sms/simulate",
        json={
            "recipient_id": "virtual-phone-2",
            "crop_id": "irish-potato",
            "message": "Test message",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Test message"


def test_unknown_crop_and_invalid_mobile_request(client):
    unknown = client.post(
        "/api/v1/advisory/mobile",
        json=full_mobile_payload(crop_id="unknown-crop"),
    )
    assert unknown.status_code == 404
    invalid = client.post(
        "/api/v1/advisory/mobile",
        json={"farmer_id": "farmer-1", "question": "What should I plant?"},
    )
    assert invalid.status_code == 422
    assert client.get("/api/v1/crops/unknown-crop").status_code == 404
    assert client.get("/api/v1/recommendations/missing").status_code == 404
