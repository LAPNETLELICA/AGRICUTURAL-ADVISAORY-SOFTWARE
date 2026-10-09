from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from integrations.database.contact_repository import (
    AgriculturalContact,
    AgriculturalContactRepository,
)
from integrations.database.tables import Base


def test_public_lookup_excludes_unverified_and_inactive_contacts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    repository = AgriculturalContactRepository(sessionmaker(bind=engine))
    expected = repository.create(
        AgriculturalContact(
            contact_id="vendor-1", name="Verified vendor", contact_type="VENDOR",
            category="fertilizer", crop_ids=["tomato"], region="Centre", location="Yaounde",
            verified=True, active=True,
        )
    )
    repository.create(
        AgriculturalContact(
            contact_id="vendor-2", name="Inactive", contact_type="VENDOR", verified=True
        )
    )

    actual = repository.find_public("VENDOR", "fertilizer", "tomato", "Centre", "Yaounde")
    assert actual == [expected]
