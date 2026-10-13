from __future__ import annotations

from pathlib import Path
from typing import Any

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase
from domain.aliases import normalize_crop_id, normalize_region_id, normalize_soil_id


class CameroonKnowledgeRepository:
    """Repository d'accès aux entités documentaires de BASE_CONNAISSANCES_AGRICOLES."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.base = CameroonKnowledgeBase(root)

    def summary(self) -> dict[str, Any]:
        return self.base.summary()

    def list_crops(self) -> list[dict[str, Any]]:
        return self.base.list_cultures()

    def get_crop(self, crop_id: str) -> dict[str, Any] | None:
        canonical_code = normalize_crop_id(crop_id)
        return self.base.get_culture(canonical_code)

    def list_regions(self) -> list[dict[str, Any]]:
        return self.base.list_regions()

    def get_region(self, region_id: str) -> dict[str, Any] | None:
        canonical_code = normalize_region_id(region_id)
        return self.base.get_region(canonical_code)

    def list_soils(self) -> list[dict[str, Any]]:
        return self.base.list_sols()

    def get_soil(self, soil_id: str) -> dict[str, Any] | None:
        canonical_code = normalize_soil_id(soil_id)
        return self.base.get_sol(canonical_code)

    def resolve_crop(self, crop_id: str) -> dict[str, Any]:
        canonical_code = normalize_crop_id(crop_id)
        return self.base.resolve_culture_links(canonical_code)
