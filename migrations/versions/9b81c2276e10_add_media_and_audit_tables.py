"""add controlled media evidence and audit tables

Revision ID: 9b81c2276e10
Revises: 7f53c0c7be74
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9b81c2276e10"
down_revision: str | None = "7f53c0c7be74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    op.add_column("trace_records", sa.Column("farmer_id", sa.String(length=100), nullable=True))
    op.create_index("ix_trace_records_farmer_id", "trace_records", ["farmer_id"])
    op.add_column("recommendations", sa.Column("farmer_id", sa.String(length=100), nullable=True))
    op.create_index("ix_recommendations_farmer_id", "recommendations", ["farmer_id"])
    op.add_column("sms_deliveries", sa.Column("farmer_id", sa.String(length=100), nullable=True))
    op.create_index("ix_sms_deliveries_farmer_id", "sms_deliveries", ["farmer_id"])
    op.create_table(
        "media_evidence",
        sa.Column("image_id", sa.String(length=100), primary_key=True),
        sa.Column("farmer_id", sa.String(length=100), nullable=False),
        sa.Column("crop_id", sa.String(length=100), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_media_evidence_farmer_created", "media_evidence", ["farmer_id", "created_at"]
    )
    op.create_index("ix_media_evidence_expires", "media_evidence", ["expires_at"])

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", json_type, nullable=False),
    )
    op.create_index("ix_audit_events_actor_created", "audit_events", ["actor_id", "created_at"])
    op.create_index("ix_audit_events_expires", "audit_events", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_sms_deliveries_farmer_id", table_name="sms_deliveries")
    op.drop_column("sms_deliveries", "farmer_id")
    op.drop_index("ix_recommendations_farmer_id", table_name="recommendations")
    op.drop_column("recommendations", "farmer_id")
    op.drop_index("ix_trace_records_farmer_id", table_name="trace_records")
    op.drop_column("trace_records", "farmer_id")
    op.drop_index("ix_audit_events_expires", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_media_evidence_expires", table_name="media_evidence")
    op.drop_index("ix_media_evidence_farmer_created", table_name="media_evidence")
    op.drop_table("media_evidence")
