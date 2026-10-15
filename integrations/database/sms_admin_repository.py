"""PostgreSQL persistence for region-scoped SMS administration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from engine.sms import (
    CameroonRegion,
    DeliveryScope,
    DeliveryScopeKind,
    SMSRegistration,
    normalize_cameroon_phone,
)
from integrations.database.tables import SMSAdminDeliveryRow, SMSRegistrationRow
from integrations.database.uow import repository_session


class PostgresSMSAdminRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    @staticmethod
    def _registration(row: SMSRegistrationRow) -> SMSRegistration:
        return SMSRegistration(
            registration_id=row.registration_id,
            phone=row.phone,
            region=CameroonRegion.parse(row.region),
            active=row.active,
        )

    def create_registration(
        self, *, phone: str, region: CameroonRegion | str, active: bool = True
    ) -> SMSRegistration:
        parsed_region = region if isinstance(region, CameroonRegion) else CameroonRegion.parse(region)
        normalized_phone = normalize_cameroon_phone(phone)
        now = datetime.now(UTC)
        row = SMSRegistrationRow(
            registration_id=str(uuid4()), phone=normalized_phone, region=parsed_region.value,
            active=active, created_at=now, updated_at=now,
        )
        registration = SMSRegistration(
            registration_id=row.registration_id,
            phone=row.phone,
            region=parsed_region,
            active=row.active,
        )
        try:
            with repository_session(self._sessions, write=True) as session:
                session.add(row)
        except IntegrityError as exc:
            raise ValueError(f"phone number {normalized_phone} is already registered") from exc
        return registration

    def list_registrations(self) -> list[SMSRegistration]:
        return self._read_registrations(
            select(SMSRegistrationRow).order_by(SMSRegistrationRow.created_at.desc())
        )

    def resolve_active_recipients(self, scope: DeliveryScope) -> list[SMSRegistration]:
        statement = select(SMSRegistrationRow).where(SMSRegistrationRow.active.is_(True))
        if scope.kind is DeliveryScopeKind.REGION:
            statement = statement.where(SMSRegistrationRow.region == scope.region.value)
        elif scope.kind is DeliveryScopeKind.REGISTRATION:
            statement = statement.where(SMSRegistrationRow.registration_id == scope.registration_id)
        return self._read_registrations(statement)

    def _read_registrations(self, statement: object) -> list[SMSRegistration]:
        with repository_session(self._sessions) as session:
            return [self._registration(row) for row in session.scalars(statement).all()]

    def create_delivery(
        self, *, registration_id: str, scope: DeliveryScope, source: str, message: str,
        status: str, alert_fingerprint: str | None = None,
    ) -> str:
        with repository_session(self._sessions, write=True) as session:
            registration = session.get(SMSRegistrationRow, registration_id)
            if registration is None:
                raise ValueError("SMS registration not found")
            delivery_id = str(uuid4())
            session.add(SMSAdminDeliveryRow(
                delivery_id=delivery_id, registration_id=registration_id, phone=registration.phone,
                scope_kind=scope.kind.value,
                scope_region=scope.region.value if scope.region else None,
                source=source, message=message, status=status,
                alert_fingerprint=alert_fingerprint, created_at=datetime.now(UTC),
            ))
        return delivery_id

    def was_alert_delivered(self, registration_id: str, alert_fingerprint: str) -> bool:
        statement = select(SMSAdminDeliveryRow.delivery_id).where(
            SMSAdminDeliveryRow.registration_id == registration_id,
            SMSAdminDeliveryRow.alert_fingerprint == alert_fingerprint,
            SMSAdminDeliveryRow.status == "sent",
        )
        with repository_session(self._sessions) as session:
            return session.scalar(statement) is not None

    def list_deliveries(self, limit: int = 100) -> list[dict[str, object]]:
        statement = select(SMSAdminDeliveryRow).order_by(SMSAdminDeliveryRow.created_at.desc()).limit(limit)
        with repository_session(self._sessions) as session:
            return [
                {
                    "delivery_id": row.delivery_id, "registration_id": row.registration_id,
                    "phone": row.phone, "scope": row.scope_kind, "region": row.scope_region,
                    "source": row.source, "message": row.message, "status": row.status,
                    "created_at": row.created_at.isoformat(),
                }
                for row in session.scalars(statement).all()
            ]


class InMemorySMSAdminRepository:
    """In-memory repository for development and environments without PostgreSQL."""

    def __init__(self) -> None:
        self._registrations: dict[str, SMSRegistration] = {}
        self._deliveries: list[dict[str, object]] = []

    def create_registration(
        self, *, phone: str, region: CameroonRegion | str, active: bool = True
    ) -> SMSRegistration:
        parsed_region = region if isinstance(region, CameroonRegion) else CameroonRegion.parse(region)
        normalized_phone = normalize_cameroon_phone(phone)
        registration = SMSRegistration(
            registration_id=str(uuid4()),
            phone=normalized_phone,
            region=parsed_region,
            active=active,
        )
        self._registrations[registration.registration_id] = registration
        return registration

    def list_registrations(self) -> list[SMSRegistration]:
        return list(reversed(list(self._registrations.values())))

    def resolve_active_recipients(self, scope: DeliveryScope) -> list[SMSRegistration]:
        recipients = [r for r in self._registrations.values() if r.active]
        if scope.kind is DeliveryScopeKind.REGION:
            return [r for r in recipients if r.region == scope.region]
        if scope.kind is DeliveryScopeKind.REGISTRATION:
            return [r for r in recipients if r.registration_id == scope.registration_id]
        return recipients

    def create_delivery(
        self, *, registration_id: str, scope: DeliveryScope, source: str, message: str,
        status: str, alert_fingerprint: str | None = None,
    ) -> str:
        registration = self._registrations.get(registration_id)
        if registration is None:
            raise ValueError("SMS registration not found")
        delivery_id = str(uuid4())
        self._deliveries.append({
            "delivery_id": delivery_id,
            "registration_id": registration_id,
            "phone": registration.phone,
            "scope": scope.kind.value,
            "region": scope.region.value if scope.region else None,
            "source": source,
            "message": message,
            "status": status,
            "alert_fingerprint": alert_fingerprint,
            "created_at": datetime.now(UTC).isoformat(),
        })
        return delivery_id

    def was_alert_delivered(self, registration_id: str, alert_fingerprint: str) -> bool:
        return any(
            d["registration_id"] == registration_id
            and d.get("alert_fingerprint") == alert_fingerprint
            and d["status"] == "sent"
            for d in self._deliveries
        )

    def list_deliveries(self, limit: int = 100) -> list[dict[str, object]]:
        return list(reversed(self._deliveries))[:limit]

