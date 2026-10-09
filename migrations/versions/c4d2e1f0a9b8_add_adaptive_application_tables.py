"""add adaptive profile, visual intelligence, learning and fiche tables

Revision ID: c4d2e1f0a9b8
Revises: 9b81c2276e10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d2e1f0a9b8"
down_revision: str | None = "9b81c2276e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("identity_type", sa.String(100), nullable=False),
        sa.Column("knowledge_level", sa.String(40), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("vocabulary_level", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "visual_reference_images",
        sa.Column("reference_id", sa.String(100), primary_key=True),
        sa.Column("knowledge_path", sa.String(1000), nullable=False, unique=True),
        sa.Column("crop_id", sa.String(100)),
        sa.Column("subject", sa.String(100)),
        sa.Column("metadata", json_type, nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_visual_reference_images_crop_id", "visual_reference_images", ["crop_id"])
    op.create_table(
        "image_analyses",
        sa.Column("analysis_id", sa.String(100), primary_key=True),
        sa.Column(
            "image_id", sa.String(100), sa.ForeignKey("media_evidence.image_id"), nullable=False
        ),
        sa.Column("farmer_id", sa.String(100), nullable=False),
        sa.Column("analysis_type", sa.String(40), nullable=False),
        sa.Column("relevant", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_image_analyses_farmer_id", "image_analyses", ["farmer_id"])
    op.create_table(
        "image_matches",
        sa.Column("match_id", sa.String(100), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(100),
            sa.ForeignKey("image_analyses.analysis_id"),
            nullable=False,
        ),
        sa.Column(
            "reference_id",
            sa.String(100),
            sa.ForeignKey("visual_reference_images.reference_id"),
            nullable=False,
        ),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
    )
    op.create_table(
        "learning_profiles",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "learning_assessments",
        sa.Column("assessment_id", sa.String(100), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("declared_level", sa.String(40), nullable=False),
        sa.Column("assessed_level", sa.String(40)),
        sa.Column("score", sa.Float()),
        sa.Column("answers", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_learning_assessments_user_id", "learning_assessments", ["user_id"])
    op.create_table(
        "curricula",
        sa.Column("curriculum_id", sa.String(100), primary_key=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("knowledge_level", sa.String(40), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "learning_progress",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("curriculum_id", sa.String(100), primary_key=True),
        sa.Column("completed_modules", json_type, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "technical_fiches",
        sa.Column("fiche_id", sa.String(100), primary_key=True),
        sa.Column("owner_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("crop_id", sa.String(100)),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("content", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_technical_fiches_owner_id", "technical_fiches", ["owner_id"])
    op.create_index("ix_technical_fiches_status", "technical_fiches", ["status"])
    op.create_index("ix_technical_fiches_crop_id", "technical_fiches", ["crop_id"])
    op.create_index("ix_technical_fiches_subject", "technical_fiches", ["subject"])


def downgrade() -> None:
    for name in (
        "ix_technical_fiches_subject",
        "ix_technical_fiches_crop_id",
        "ix_technical_fiches_status",
        "ix_technical_fiches_owner_id",
    ):
        op.drop_index(name, table_name="technical_fiches")
    op.drop_table("technical_fiches")
    op.drop_table("learning_progress")
    op.drop_table("curricula")
    op.drop_index("ix_learning_assessments_user_id", table_name="learning_assessments")
    op.drop_table("learning_assessments")
    op.drop_table("learning_profiles")
    op.drop_table("image_matches")
    op.drop_index("ix_image_analyses_farmer_id", table_name="image_analyses")
    op.drop_table("image_analyses")
    op.drop_index("ix_visual_reference_images_crop_id", table_name="visual_reference_images")
    op.drop_table("visual_reference_images")
    op.drop_table("user_profiles")
