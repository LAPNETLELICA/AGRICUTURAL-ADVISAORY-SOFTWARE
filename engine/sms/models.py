"""Transport-independent SMS administration values."""

from dataclasses import dataclass
from enum import StrEnum


class CameroonRegion(StrEnum):
    ADAMAWA = "Adamawa"
    CENTRE = "Centre"
    EAST = "East"
    FAR_NORTH = "Far North"
    LITTORAL = "Littoral"
    NORTH = "North"
    NORTH_WEST = "North-West"
    SOUTH = "South"
    SOUTH_WEST = "South-West"
    WEST = "West"

    @classmethod
    def parse(cls, value: str) -> "CameroonRegion":
        candidate = value.strip().casefold().replace("_", "-")
        for region in cls:
            if candidate == region.value.casefold():
                return region
        raise ValueError("a valid Cameroon region is required")


class DeliveryScopeKind(StrEnum):
    REGISTRATION = "registration"
    REGION = "region"
    CAMEROON = "cameroon"


@dataclass(frozen=True, slots=True)
class DeliveryScope:
    kind: DeliveryScopeKind
    registration_id: str | None = None
    region: CameroonRegion | None = None

    @classmethod
    def registration(cls, registration_id: str) -> "DeliveryScope":
        return cls(kind=DeliveryScopeKind.REGISTRATION, registration_id=registration_id)

    @classmethod
    def region_scope(cls, region: CameroonRegion | str) -> "DeliveryScope":
        return cls(
            kind=DeliveryScopeKind.REGION,
            region=region if isinstance(region, CameroonRegion) else CameroonRegion.parse(region),
        )

    @classmethod
    def cameroon(cls) -> "DeliveryScope":
        return cls(kind=DeliveryScopeKind.CAMEROON)

    def __post_init__(self) -> None:
        if self.kind is DeliveryScopeKind.REGISTRATION and not self.registration_id:
            raise ValueError("registration scope requires a registration ID")
        if self.kind is DeliveryScopeKind.REGION and self.region is None:
            raise ValueError("region scope requires a Cameroon region")
        if self.kind is DeliveryScopeKind.CAMEROON and any(
            (self.registration_id, self.region)
        ):
            raise ValueError("Cameroon scope cannot contain a recipient target")


@dataclass(frozen=True, slots=True)
class SMSRegistration:
    registration_id: str
    phone: str
    region: CameroonRegion
    active: bool = True


@dataclass(frozen=True, slots=True)
class ManualBroadcast:
    message: str
    scope: DeliveryScope


@dataclass(frozen=True, slots=True)
class ProactiveAlert:
    message: str
    scope: DeliveryScope
    fingerprint: str
    provenance: str
    validated: bool
