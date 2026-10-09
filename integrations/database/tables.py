"""SQLAlchemy tables for V1 operational persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class containing all database table metadata."""


JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class AgriculturalContactRow(Base):
    """Verified specialist or vendor available for recommendation support."""

    __tablename__ = "agricultural_contacts"
    __table_args__ = (
        Index("ix_agricultural_contacts_type_category", "contact_type", "category"),
        Index("ix_agricultural_contacts_region", "region"),
        Index("ix_agricultural_contacts_public", "verified", "active", "contact_type"),
    )
    contact_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crop_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CropPassportRow(Base):
    __tablename__ = "crop_passports"
    __table_args__ = (
        UniqueConstraint(
            "farmer_id",
            "crop_id",
            "plot_ref",
            name="uq_crop_passports_farmer_crop_plot",
        ),
    )

    passport_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    farmer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    plot_ref: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    current_stage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        nullable=False,
    )


class TraceRecordRow(Base):
    __tablename__ = "trace_records"

    trace_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    farmer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    final_recommendation_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        nullable=False,
    )


class RecommendationRow(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    farmer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    trace_id: Mapped[str] = mapped_column(
        ForeignKey(
            "trace_records.trace_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        nullable=False,
    )


class HistoryEventRow(Base):
    __tablename__ = "history_events"
    __table_args__ = (
        Index(
            "ix_history_events_farmer_crop_recorded",
            "farmer_id",
            "crop_id",
            "recorded_at",
        ),
        Index(
            "ix_history_events_farmer_family_recorded",
            "farmer_id",
            "crop_family",
            "recorded_at",
        ),
    )

    event_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    farmer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    crop_family: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    trace_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        nullable=False,
    )


class SMSDeliveryRow(Base):
    __tablename__ = "sms_deliveries"
    __table_args__ = (
        Index(
            "ix_sms_deliveries_recipient_delivered",
            "recipient_id",
            "delivered_at",
        ),
    )

    delivery_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    recipient_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    farmer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        nullable=False,
    )


class MediaEvidenceRow(Base):
    __tablename__ = "media_evidence"
    __table_args__ = (
        Index("ix_media_evidence_farmer_created", "farmer_id", "created_at"),
        Index("ix_media_evidence_expires", "expires_at"),
    )

    image_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_actor_created", "actor_id", "created_at"),
        Index("ix_audit_events_expires", "expires_at"),
    )

    event_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)


# These tables store application state and indexes.  Agricultural source material
# deliberately remains in ``BASE_CONNAISSANCES_AGRICOLES/``.
class UserProfileRow(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    identity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    knowledge_level: Mapped[str] = mapped_column(String(40), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    vocabulary_level: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImageAnalysisRow(Base):
    __tablename__ = "image_analyses"

    analysis_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("media_evidence.image_id"), nullable=False)
    farmer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    analysis_type: Mapped[str] = mapped_column(String(40), nullable=False)
    relevant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VisualReferenceImageRow(Base):
    __tablename__ = "visual_reference_images"

    reference_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    knowledge_path: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    crop_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON_DOCUMENT, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImageMatchRow(Base):
    __tablename__ = "image_matches"

    match_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("image_analyses.analysis_id"), nullable=False
    )
    reference_id: Mapped[str] = mapped_column(
        ForeignKey("visual_reference_images.reference_id"), nullable=False
    )
    similarity: Mapped[float] = mapped_column(nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)


class LearningProfileRow(Base):
    __tablename__ = "learning_profiles"
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearningAssessmentRow(Base):
    __tablename__ = "learning_assessments"
    assessment_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    declared_level: Mapped[str] = mapped_column(String(40), nullable=False)
    assessed_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    score: Mapped[float | None] = mapped_column(nullable=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CurriculumRow(Base):
    __tablename__ = "curricula"
    curriculum_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    knowledge_level: Mapped[str] = mapped_column(String(40), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearningProgressRow(Base):
    __tablename__ = "learning_progress"
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    curriculum_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    completed_modules: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TechnicalFicheRow(Base):
    __tablename__ = "technical_fiches"
    fiche_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    crop_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
