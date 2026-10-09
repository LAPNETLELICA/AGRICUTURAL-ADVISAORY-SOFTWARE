"""Persistence and relevance lookup for verified agricultural contacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from integrations.database.tables import AgriculturalContactRow
from integrations.database.uow import repository_session


@dataclass(frozen=True, slots=True)
class AgriculturalContact:
    contact_id: str
    name: str
    contact_type: str
    description: str | None = None
    specialization: str | None = None
    category: str | None = None
    crop_ids: list[str] = field(default_factory=list)
    region: str | None = None
    location: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    verified: bool = False
    active: bool = False


class AgriculturalContactRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def create(self, contact: AgriculturalContact) -> AgriculturalContact:
        now = datetime.now(UTC)
        with repository_session(self._sessions, write=True) as session:
            session.add(AgriculturalContactRow(**asdict(contact), created_at=now, updated_at=now))
        return contact

    def list(self) -> list[AgriculturalContact]:
        with repository_session(self._sessions) as session:
            rows = session.scalars(select(AgriculturalContactRow)).all()
            return [self._to_contact(row) for row in rows]

    def get(self, contact_id: str) -> AgriculturalContact | None:
        with repository_session(self._sessions) as session:
            row = session.get(AgriculturalContactRow, contact_id)
            return self._to_contact(row) if row else None

    def update(self, contact_id: str, **changes: object) -> AgriculturalContact | None:
        with repository_session(self._sessions, write=True) as session:
            row = session.get(AgriculturalContactRow, contact_id)
            if row is None:
                return None
            for name, value in changes.items():
                if name in AgriculturalContact.__dataclass_fields__:
                    setattr(row, name, value)
            row.updated_at = datetime.now(UTC)
            session.flush()
            return self._to_contact(row)

    def find_public(
        self, contact_type: str, category: str | None, crop_id: str | None,
        region: str | None, location: str | None,
    ) -> list[AgriculturalContact]:
        statement = select(AgriculturalContactRow).where(
            AgriculturalContactRow.contact_type == contact_type,
            AgriculturalContactRow.verified.is_(True),
            AgriculturalContactRow.active.is_(True),
        )
        with repository_session(self._sessions) as session:
            contacts = [self._to_contact(row) for row in session.scalars(statement).all()]
        return sorted(
            contacts,
            key=lambda item: (
                item.category != category,
                crop_id not in item.crop_ids if crop_id else True,
                item.region != region,
                item.location != location,
                item.name.casefold(),
            ),
        )

    @staticmethod
    def _to_contact(row: AgriculturalContactRow) -> AgriculturalContact:
        return AgriculturalContact(
            **{name: getattr(row, name) for name in AgriculturalContact.__dataclass_fields__}
        )
