from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from domain.models import AgriculturalRule, SourceReference

TreeCode = Literal["T1", "T2", "T3", "T4", "T5", "T6", "T7"]


class KnowledgeQuery(BaseModel):
    crop_id: str = Field(min_length=1, description="Identifiant ou alias de la culture (ex: CULT_TOMATE, tomate, potato)")
    trees: list[TreeCode] = Field(
        default_factory=lambda: ["T1", "T2", "T3", "T4", "T5", "T6", "T7"],
        description="Liste des arbres agronomiques à interroger (T1 à T7)",
    )
    region_id: str | None = Field(default=None, description="Identifiant ou alias de la région (ex: REG_OU, ouest)")
    soil_id: str | None = Field(default=None, description="Identifiant ou alias du sol (ex: SOL_VOLCANIQUE, andosol)")


class KnowledgeVersion(BaseModel):
    knowledge_release: str
    schema_version: str
    status: str
    release_date: str = ""
    sha256_hash: str = ""
    author: str = ""
    statistics: dict[str, int]
    sources: list[str] = Field(default_factory=list)


class KnowledgeQueryResponse(BaseModel):
    knowledge_release: str
    crop_id: str
    requested_trees: list[TreeCode]
    rules: list[AgriculturalRule] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
