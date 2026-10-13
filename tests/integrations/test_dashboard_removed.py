from pathlib import Path

from api.app import create_app
from engine.config import Settings


def test_backend_no_longer_serves_dashboard_pages() -> None:
    root = Path(__file__).resolve().parents[2]
    app = create_app(
        Settings(environment="test", knowledge_path=root / "BASE_CONNAISSANCES_AGRICOLES")
    )
    paths = {route.path for route in app.routes}

    assert "/dashboard" not in paths
    assert "/dashboard/sms-receiver" not in paths
    assert "/api/v1/health" in paths
