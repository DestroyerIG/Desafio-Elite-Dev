"""Allow multiple payment attempts per reservation.

Revision ID: 20260816_0002
Revises: 20260813_0001
Create Date: 2026-08-16
"""
from collections.abc import Sequence

from alembic import op


revision: str = "20260816_0002"
down_revision: str | None = "20260813_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_payments_reservation_id",
        "payments",
        type_="unique",
    )
    op.create_index(
        "ix_payments_reservation_id",
        "payments",
        ["reservation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_payments_reservation_id", table_name="payments")
    op.create_unique_constraint(
        "uq_payments_reservation_id",
        "payments",
        ["reservation_id"],
    )
