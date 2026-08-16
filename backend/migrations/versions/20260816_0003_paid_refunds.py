"""Add paid reservation refunds.

Revision ID: 20260816_0003
Revises: 20260816_0002
Create Date: 2026-08-16
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260816_0003"
down_revision: str | None = "20260816_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


refund_status = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "FAILED",
    name="refund_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("ALTER TYPE reservation_status ADD VALUE IF NOT EXISTS 'REFUNDED'")
    op.execute("ALTER TYPE ticket_status ADD VALUE IF NOT EXISTS 'REFUNDED'")
    refund_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", refund_status, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="amount_non_negative"),
        sa.CheckConstraint(
            "(status = 'PENDING' AND processed_at IS NULL) "
            "OR (status <> 'PENDING' AND processed_at IS NOT NULL)",
            name="processed_at_matches_status",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"],
            name="fk_refunds_payment_id_payments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_refunds_reservation_id_reservations",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_refunds"),
        sa.UniqueConstraint("payment_id", name="uq_refunds_payment_id"),
        sa.UniqueConstraint("reservation_id", name="uq_refunds_reservation_id"),
    )


def downgrade() -> None:
    op.drop_table("refunds")
    refund_status.drop(op.get_bind(), checkfirst=True)

    op.execute("UPDATE reservations SET status = 'CANCELLED' WHERE status = 'REFUNDED'")
    op.execute("UPDATE tickets SET status = 'CANCELLED' WHERE status = 'REFUNDED'")

    op.alter_column(
        "reservations",
        "status",
        type_=sa.String(),
        postgresql_using="status::text",
    )
    op.execute("DROP TYPE reservation_status")
    old_reservation_status = sa.Enum(
        "PENDING", "PAID", "CANCELLED", "EXPIRED", name="reservation_status"
    )
    old_reservation_status.create(op.get_bind())
    op.alter_column(
        "reservations",
        "status",
        type_=old_reservation_status,
        postgresql_using="status::reservation_status",
    )

    op.drop_constraint(
        op.f("ck_tickets_used_at_matches_status"),
        "tickets",
        type_="check",
    )
    op.alter_column(
        "tickets",
        "status",
        type_=sa.String(),
        postgresql_using="status::text",
    )
    op.execute("DROP TYPE ticket_status")
    old_ticket_status = sa.Enum(
        "ACTIVE", "USED", "CANCELLED", name="ticket_status"
    )
    old_ticket_status.create(op.get_bind())
    op.alter_column(
        "tickets",
        "status",
        type_=old_ticket_status,
        postgresql_using="status::ticket_status",
    )
    op.create_check_constraint(
        op.f("ck_tickets_used_at_matches_status"),
        "tickets",
        "(status = 'USED' AND used_at IS NOT NULL) "
        "OR (status <> 'USED' AND used_at IS NULL)",
    )
