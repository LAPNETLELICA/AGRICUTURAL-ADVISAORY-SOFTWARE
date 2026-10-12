"""Persistence tests for regional SMS registrations and deliveries."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.sms import DeliveryScope
from integrations.database.sms_admin_repository import PostgresSMSAdminRepository
from integrations.database.tables import Base


def repository() -> PostgresSMSAdminRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return PostgresSMSAdminRepository(sessionmaker(engine))


def test_region_resolution_returns_only_active_exact_matches() -> None:
    sms_repository = repository()
    south = sms_repository.create_registration(phone="+237677123456", region="South")
    sms_repository.create_registration(phone="+237677123457", region="Centre")
    sms_repository.create_registration(phone="+237677123458", region="South", active=False)

    recipients = sms_repository.resolve_active_recipients(DeliveryScope.region_scope("South"))

    assert [item.phone for item in recipients] == ["+237677123456"]
    assert recipients[0].registration_id == south.registration_id


def test_registration_is_normalized_and_listed_for_admin_use() -> None:
    sms_repository = repository()

    registration = sms_repository.create_registration(phone="6 77 12 34 56", region="South")

    assert registration.phone == "+237677123456"
    assert sms_repository.list_registrations() == [registration]


def test_alert_fingerprint_is_retained_for_deduplication() -> None:
    sms_repository = repository()
    registration = sms_repository.create_registration(phone="+237677123456", region="South")

    sms_repository.create_delivery(
        registration_id=registration.registration_id,
        scope=DeliveryScope.region_scope("South"),
        source="automatic",
        message="Rainfall alert",
        status="sent",
        alert_fingerprint="weather:south:2026-10-09",
    )

    assert (
        sms_repository.was_alert_delivered(
            registration.registration_id, "weather:south:2026-10-09"
        )
        is True
    )
