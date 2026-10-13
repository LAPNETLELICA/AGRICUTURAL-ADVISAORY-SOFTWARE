from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class CompatibleBaseModel(BaseModel):
    """Classe de base compatible avec Pydantic v1 (Debian/Parrot) et Pydantic v2 (prod)."""

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        if hasattr(super(), "model_dump"):
            return super().model_dump(*args, **kwargs)  # type: ignore[misc]
        # Pydantic v1 fallback
        return json.loads(self.json())

    def model_copy(self, *args, **kwargs) -> Any:
        if hasattr(super(), "model_copy"):
            return super().model_copy(*args, **kwargs)  # type: ignore[misc]
        # Pydantic v1 fallback
        return self.copy(*args, **kwargs)


class TreeId(str, Enum):
    T1_PROFILE = "T1"
    T2_SOIL = "T2"
    T3_REGION = "T3"
    T4_TOPOGRAPHY = "T4"
    T5_CLIMATE = "T5"
    T6_TIMING = "T6"
    T7_PRACTICES = "T7"


class KnowledgeStatus(str, Enum):
    DISCOVERED = "discovered"
    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    PENDING_REVIEW = "pending_review"
    VALIDATED = "validated"
    PUBLISHED = "published"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class ChangeType(str, Enum):
    ADDITION = "addition"
    UPDATE = "update"
    CORRECTION = "correction"
    DEPRECATION = "deprecation"


class ConflictLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConditionSpec(CompatibleBaseModel):
    field: str
    operator: str  # eq, neq, gt, gte, lt, lte, in, not_in, between, exists
    value: Any = None


class CandidateRecommendation(CompatibleBaseModel):
    candidate_id: str
    type: str  # advisory, soil_action, practice, risk_alert, timing
    name: str
    summary: str
    actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)


class SourceReference(CompatibleBaseModel):
    source_id: str
    organization: str
    title: str
    canonical_url: str | None = None
    document_url: str | None = None
    document_type: str = "guide_technique"
    page: str | None = None
    section: str | None = None
    reference: str = ""
    publication_date: str | None = None
    authority_level: str = "national_official"


class AgriculturalRule(CompatibleBaseModel):
    rule_id: str
    crop_id: str
    tree: TreeId
    domain: str = ""
    version: str = "1.0.0"
    status: KnowledgeStatus = KnowledgeStatus.PUBLISHED
    priority: int = 100
    conditions: list[ConditionSpec] = Field(default_factory=list)
    candidate: CandidateRecommendation
    constraints: list[dict[str, Any]] = Field(default_factory=list)
    source_refs: list[SourceReference] = Field(default_factory=list)
    region_ids: list[str] = Field(default_factory=list)
    soil_ids: list[str] = Field(default_factory=list)
    variety_ids: list[str] = Field(default_factory=list)
    climate_zone_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: datetime | None = None
    validated_by: str | None = None
    confidence: float = 1.0
    notes: str = ""


class CropProfile(CompatibleBaseModel):
    crop_id: str
    name: str
    scientific_name: str
    family_code: str
    cycle_length_days: int = 90
    growth_stages: list[str] = Field(default_factory=list)
    tolerances: dict[str, Any] = Field(default_factory=dict)
    varieties: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    status: KnowledgeStatus = KnowledgeStatus.PUBLISHED
    source: SourceReference | None = None


class RegionProfile(CompatibleBaseModel):
    region_id: str
    name: str
    capital: str
    agroecological_zones: list[str] = Field(default_factory=list)
    rainfall_mm: dict[str, Any] = Field(default_factory=dict)
    temperatures_c: dict[str, Any] = Field(default_factory=dict)
    localities: list[dict[str, Any]] = Field(default_factory=list)


class SoilProfile(CompatibleBaseModel):
    soil_id: str
    name: str
    code_fao: str = ""
    characteristics: dict[str, Any] = Field(default_factory=dict)
    favorable_crops: list[str] = Field(default_factory=list)
    drainage: str = ""
    ph_typical: list[float] = Field(default_factory=list)


class SourceOrganization(CompatibleBaseModel):
    organization_id: str
    name: str
    acronym: str
    country: str = "Cameroun"
    authority_level: str = "gouvernemental"
    website: str | None = None


class SourceDocument(CompatibleBaseModel):
    source_id: str
    organization_id: str
    title: str
    publication_year: int | None = None
    canonical_url: str | None = None
    document_type: str = "guide"
    authority_level: str = "national_official"
    content_hash: str | None = None
    language: str = "fr"


class KnowledgeItem(CompatibleBaseModel):
    item_id: str
    entity_type: str  # crop, rule, soil, practice
    entity_id: str
    field_name: str
    field_value: Any
    source_id: str
    status: KnowledgeStatus = KnowledgeStatus.PUBLISHED
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationReview(CompatibleBaseModel):
    review_id: str
    entity_type: str
    entity_id: str
    field_name: str
    old_value: Any
    new_value: Any
    old_source_id: str | None = None
    new_source_id: str
    conflict_level: ConflictLevel = ConflictLevel.NONE
    change_type: ChangeType = ChangeType.UPDATE
    status: KnowledgeStatus = KnowledgeStatus.PENDING_REVIEW
    reviewed_by: str | None = None
    reviewer_notes: str | None = None
    reviewed_at: datetime | None = None


class KnowledgeRelease(CompatibleBaseModel):
    release_id: str  # ex: CM-KNOWLEDGE-2026.10.1
    schema_version: str = "2.0.0"
    status: KnowledgeStatus = KnowledgeStatus.PUBLISHED
    release_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sha256_hash: str
    author: str = "Comité Scientifique et Agronomique AgriSense"
    total_crops: int
    total_rules: int
    total_soils: int
    total_regions: int
    sources: list[str] = Field(default_factory=list)
    changelog: list[str] = Field(default_factory=list)
