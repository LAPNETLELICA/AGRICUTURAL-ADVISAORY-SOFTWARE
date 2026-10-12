"""add agricultural contacts

Revision ID: e1a3b6d9f2c4
Revises: 9b81c2276e10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e1a3b6d9f2c4"
down_revision: str | None = "9b81c2276e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    op.create_table(
        "agricultural_contacts",
        sa.Column("contact_id", sa.String(length=100), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("contact_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specialization", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("crop_ids", json_type, nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("whatsapp", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_agricultural_contacts_type_category",
        "agricultural_contacts",
        ["contact_type", "category"],
    )
    op.create_index("ix_agricultural_contacts_region", "agricultural_contacts", ["region"])
    op.create_index(
        "ix_agricultural_contacts_public",
        "agricultural_contacts",
        ["verified", "active", "contact_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_agricultural_contacts_public", table_name="agricultural_contacts")
    op.drop_index("ix_agricultural_contacts_region", table_name="agricultural_contacts")
    op.drop_index("ix_agricultural_contacts_type_category", table_name="agricultural_contacts")
    op.drop_table("agricultural_contacts")
