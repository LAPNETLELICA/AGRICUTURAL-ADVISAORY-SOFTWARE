"""Merge contact and adaptive-application migration heads.

Revision ID: 3f6a9c2d1e0b
Revises: c4d2e1f0a9b8, e1a3b6d9f2c4
"""

from collections.abc import Sequence

revision: str = "3f6a9c2d1e0b"
down_revision: tuple[str, str] = ("c4d2e1f0a9b8", "e1a3b6d9f2c4")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass