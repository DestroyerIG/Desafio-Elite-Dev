"""Create the initial domain schema.

Revision ID: 20260813_0001
Revises:
Create Date: 2026-08-13
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260813_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role = sa.Enum("ORGANIZER", "CUSTOMER", "GATE", name="user_role")
event_status = sa.Enum("DRAFT", "PUBLISHED", "CANCELLED", name="event_status")
reservation_status = sa.Enum("PENDING", "PAID", "CANCELLED", "EXPIRED", name="reservation_status")
payment_status = sa.Enum("APPROVED", "DECLINED", name="payment_status")
ticket_status = sa.Enum("ACTIVE", "USED", "CANCELLED", name="ticket_status")
validation_result = sa.Enum(
    "VALID", "INVALID", "ALREADY_USED", "WRONG_EVENT", name="validation_result"
)


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
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
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organizer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("venue_name", sa.String(length=255), nullable=False),
        sa.Column("venue_address", sa.Text(), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("available_tickets", sa.Integer(), nullable=False),
        sa.Column("ticket_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", event_status, nullable=False),
        *timestamps(),
        sa.CheckConstraint("capacity > 0", name="capacity_positive"),
        sa.CheckConstraint(
            "available_tickets >= 0", name="available_tickets_non_negative"
        ),
        sa.CheckConstraint(
            "available_tickets <= capacity", name="available_tickets_within_capacity"
        ),
        sa.CheckConstraint("ticket_price >= 0", name="ticket_price_non_negative"),
        sa.ForeignKeyConstraint(
            ["organizer_id"], ["users.id"], name="fk_events_organizer_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
        sa.UniqueConstraint(
            "organizer_id",
            "external_provider",
            "external_id",
            name="uq_events_organizer_external_event",
        ),
    )
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"], unique=False)

    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", reservation_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
        sa.CheckConstraint(
            "total_amount = quantity * unit_price", name="total_matches_quantity"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["users.id"], name="fk_reservations_customer_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name="fk_reservations_event_id_events", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservations"),
    )
    op.create_index("ix_reservations_customer_id", "reservations", ["customer_id"], unique=False)
    op.create_index("ix_reservations_event_id", "reservations", ["event_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("amount >= 0", name="amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_payments_reservation_id_reservations",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.UniqueConstraint("reservation_id", name="uq_payments_reservation_id"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_code", sa.String(length=32), nullable=False),
        sa.Column("qr_token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "(status = 'USED' AND used_at IS NOT NULL) OR (status <> 'USED' AND used_at IS NULL)",
            name="used_at_matches_status",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name="fk_tickets_event_id_events", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_tickets_owner_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_tickets_reservation_id_reservations",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tickets"),
        sa.UniqueConstraint("public_code", name="uq_tickets_public_code"),
        sa.UniqueConstraint("qr_token_hash", name="uq_tickets_qr_token_hash"),
    )
    op.create_index("ix_tickets_event_id", "tickets", ["event_id"], unique=False)
    op.create_index("ix_tickets_owner_id", "tickets", ["owner_id"], unique=False)
    op.create_index("ix_tickets_reservation_id", "tickets", ["reservation_id"], unique=False)

    op.create_table(
        "ticket_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], name="fk_ticket_shares_ticket_id_tickets", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ticket_shares"),
        sa.UniqueConstraint("token_hash", name="uq_ticket_shares_token_hash"),
    )
    op.create_index("ix_ticket_shares_ticket_id", "ticket_shares", ["ticket_id"], unique=False)

    op.create_table(
        "ticket_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gate_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", validation_result, nullable=False),
        sa.Column(
            "validated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name="fk_ticket_validations_event_id_events", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["gate_user_id"],
            ["users.id"],
            name="fk_ticket_validations_gate_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name="fk_ticket_validations_ticket_id_tickets",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ticket_validations"),
    )
    op.create_index("ix_ticket_validations_event_id", "ticket_validations", ["event_id"], unique=False)
    op.create_index(
        "ix_ticket_validations_gate_user_id", "ticket_validations", ["gate_user_id"], unique=False
    )
    op.create_index("ix_ticket_validations_ticket_id", "ticket_validations", ["ticket_id"], unique=False)


def downgrade() -> None:
    op.drop_table("ticket_validations")
    op.drop_table("ticket_shares")
    op.drop_table("tickets")
    op.drop_table("payments")
    op.drop_table("reservations")
    op.drop_table("events")
    op.drop_table("users")

    validation_result.drop(op.get_bind(), checkfirst=True)
    ticket_status.drop(op.get_bind(), checkfirst=True)
    payment_status.drop(op.get_bind(), checkfirst=True)
    reservation_status.drop(op.get_bind(), checkfirst=True)
    event_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
