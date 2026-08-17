"""Allow organizer-created events without an external catalog reference.

Revision ID: 20260817_0005
Revises: 20260817_0004
Create Date: 2026-08-17
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260817_0005"
down_revision: str | None = "20260817_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "events",
        "external_provider",
        existing_type=sa.String(length=50),
        nullable=True,
    )
    op.alter_column(
        "events",
        "external_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.create_check_constraint(
        "external_reference_complete",
        "events",
        "(external_provider IS NULL AND external_id IS NULL) OR "
        "(external_provider IS NOT NULL AND external_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "external_reference_complete",
        "events",
        type_="check",
    )
    op.execute(
        "UPDATE events "
        "SET external_provider = 'internal', external_id = id::text "
        "WHERE external_provider IS NULL AND external_id IS NULL"
    )
    op.alter_column(
        "events",
        "external_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "events",
        "external_provider",
        existing_type=sa.String(length=50),
        nullable=False,
    )
