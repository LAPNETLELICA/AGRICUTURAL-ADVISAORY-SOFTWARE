from pathlib import Path


def test_dashboard_exposes_number_registration_and_previewed_manual_sms_controls() -> None:
    page = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert "/api/v1/admin/sms/registrations" in page
    assert "/api/v1/admin/sms/broadcasts/preview" in page
    assert "/api/v1/admin/sms/broadcasts/send" in page
    assert "Add number" in page
    assert "Preview recipients" in page
    assert "Send SMS" in page
