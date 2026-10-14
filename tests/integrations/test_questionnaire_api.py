import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_questionnaire_start_and_completion_return_recommendation(container) -> None:
    with TestClient(create_app(container.settings, container)) as client:
        start = client.post(
            "/api/v1/questionnaire/start",
            json={"farmer_id": "farmer-1", "region": "West", "locality": "Bafoussam"},
        )
        assert start.status_code == 200
        assert start.json()["step"]["accepts_free_text"] is True
        complete = client.post(
            "/api/v1/questionnaire/complete",
            json={
                "context": {
                    "farmer_id": "farmer-1",
                    "crop_id": "irish-potato",
                    "question": "How can I improve my yield?",
                    "region": "West",
                    "locality": "Bafoussam",
                }
            },
        )
        assert complete.status_code == 200, complete.text
        assert complete.json()["complete"] is True
        assert complete.json()["recommendation"]["primary"]


@pytest.mark.anyio
async def test_questionnaire_start_works_with_asgi_transport(container) -> None:
    app = create_app(container.settings, container)
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/questionnaire/start",
                json={"farmer_id": "farmer-1", "region": "West", "locality": "Bafoussam"},
            )

    assert response.status_code == 200
    assert response.json()["step"]["key"] == "intent"
