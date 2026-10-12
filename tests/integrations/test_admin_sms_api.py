from fastapi.testclient import TestClient

from api.app import create_app
from engine.sms import SMSRegistration


class FakeSMSRepository:
    def __init__(self) -> None:
        self.items: list[SMSRegistration] = []

    def create_registration(self, **values: object) -> SMSRegistration:
        from engine.sms import CameroonRegion, normalize_cameroon_phone

        item = SMSRegistration(
            registration_id="registration-1",
            phone=normalize_cameroon_phone(str(values["phone"])),
            region=CameroonRegion.parse(str(values["region"])),
            active=bool(values["active"]),
        )
        self.items.append(item)
        return item

    def list_registrations(self) -> list[SMSRegistration]:
        return self.items

    def resolve_active_recipients(self, scope):
        return [
            item
            for item in self.items
            if item.active and (scope.region is None or item.region == scope.region)
        ]

    def create_delivery(self, **values: object) -> str:
        return "delivery-1"


def test_admin_can_register_and_list_a_regional_sms_number(container) -> None:
    app = create_app(container.settings, container)
    app.state.sms_admin_repository = FakeSMSRepository()
    client = TestClient(app)

    created = client.post(
        "/api/v1/admin/sms/registrations",
        json={"phone": "6 77 12 34 56", "region": "South"},
    )

    assert created.status_code == 201
    assert created.json()["phone"] == "+237677123456"
    assert created.json()["region"] == "South"
    assert client.get("/api/v1/admin/sms/registrations").json()[0]["registration_id"] == "registration-1"


def test_admin_preview_counts_only_the_selected_active_region(container) -> None:
    app = create_app(container.settings, container)
    repository = FakeSMSRepository()
    repository.create_registration(phone="677123456", region="South", active=True)
    repository.create_registration(phone="677123457", region="Centre", active=True)
    repository.create_registration(phone="677123458", region="South", active=False)
    app.state.sms_admin_repository = repository

    response = TestClient(app).post(
        "/api/v1/admin/sms/broadcasts/preview",
        json={"message": "Rain expected", "scope": {"kind": "region", "region": "South"}},
    )

    assert response.status_code == 200
    assert response.json()["recipient_count"] == 1
    assert response.json()["region"] == "South"


def test_admin_send_delivers_only_to_the_selected_region(container) -> None:
    app = create_app(container.settings, container)
    repository = FakeSMSRepository()
    repository.create_registration(phone="677123456", region="South", active=True)
    repository.create_registration(phone="677123457", region="Centre", active=True)
    app.state.sms_admin_repository = repository

    response = TestClient(app).post(
        "/api/v1/admin/sms/broadcasts/send",
        json={"message": "Rain expected", "scope": {"kind": "region", "region": "South"}},
    )

    assert response.status_code == 200
    assert response.json()["sent"] == 1
    assert response.json()["failed"] == 0
