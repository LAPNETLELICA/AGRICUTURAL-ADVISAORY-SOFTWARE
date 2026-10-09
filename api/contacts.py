"""Authenticated discovery of verified agricultural contacts."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.security import PrincipalDependency

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class ContactCard(BaseModel):
    name: str
    description: str | None = None
    specialization: str | None = None
    category: str | None = None
    region: str | None = None
    location: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None


@router.get("/{contact_type}", response_model=list[ContactCard])
def list_contacts(
    contact_type: str, request: Request, principal: PrincipalDependency,
    category: str | None = None, crop_id: str | None = None, region: str | None = None,
    location: str | None = None,
) -> list[ContactCard]:
    del principal
    if contact_type not in {"specialists", "vendors"}:
        raise HTTPException(status_code=404, detail="contact type not found")
    repository = getattr(request.app.state, "contact_repository", None)
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database persistence is not configured",
        )
    kind = "SPECIALIST" if contact_type == "specialists" else "VENDOR"
    contacts = repository.find_public(kind, category, crop_id, region, location)
    return [ContactCard(**asdict(item)) for item in contacts]
