from pathlib import Path


def test_dashboard_pages_load_public_api_configuration() -> None:
    dashboard = Path("dashboard")
    config = (dashboard / "config.js").read_text(encoding="utf-8")
    index = (dashboard / "index.html").read_text(encoding="utf-8")
    receiver = (dashboard / "receiver.html").read_text(encoding="utf-8")

    assert "window.APP_CONFIG" in config
    assert "API_BASE_URL" in config
    assert "API_KEY" not in config
    assert 'src="config.js"' in index
    assert 'src="config.js"' in receiver
    assert "apiUrl(url)" in index
    assert "apiUrl('/api/v1/sms/inbox/'" in receiver
