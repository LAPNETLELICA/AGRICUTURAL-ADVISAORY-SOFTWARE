"""add regional SMS registration and delivery tables

Revision ID: f2d8a3c1b9e7
Revises: 3f6a9c2d1e0b
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2d8a3c1b9e7"
down_revision: str | None = "3f6a9c2d1e0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sms_registrations",
        sa.Column("registration_id", sa.String(length=100), primary_key=True),
        sa.Column("phone", sa.String(length=20), nullable=False, unique=True),
        sa.Column("region", sa.String(length=20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sms_registrations_region_active", "sms_registrations", ["region", "active"])
    op.create_table(
        "sms_admin_deliveries",
        sa.Column("delivery_id", sa.String(length=100), primary_key=True),
        sa.Column("registration_id", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("scope_kind", sa.String(length=20), nullable=False),
        sa.Column("scope_region", sa.String(length=20), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("alert_fingerprint", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["sms_registrations.registration_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("registration_id", "alert_fingerprint", name="uq_sms_alert_fingerprint"),
    )
    op.create_index("ix_sms_admin_deliveries_registration_created", "sms_admin_deliveries", ["registration_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_sms_admin_deliveries_registration_created", table_name="sms_admin_deliveries")
    op.drop_table("sms_admin_deliveries")
    op.drop_index("ix_sms_registrations_region_active", table_name="sms_registrations")
    op.drop_table("sms_registrations")
