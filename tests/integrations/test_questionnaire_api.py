from fastapi.testclient import TestClient

from api.app import create_app


def test_questionnaire_start_and_completion_return_recommendation(container) -> None:
    client = TestClient(create_app(container.settings, container))
    start = client.post("/api/v1/questionnaire/start", json={"farmer_id": "farmer-1", "region": "West", "locality": "Bafoussam"})
    assert start.status_code == 200
    assert start.json()["step"]["accepts_free_text"] is True
    complete = client.post("/api/v1/questionnaire/complete", json={"context": {"farmer_id": "farmer-1", "crop_id": "irish-potato", "question": "How can I improve my yield?", "region": "West", "locality": "Bafoussam"}})
    assert complete.status_code == 200, complete.text
    assert complete.json()["complete"] is True
    assert complete.json()["recommendation"]["primary"]
