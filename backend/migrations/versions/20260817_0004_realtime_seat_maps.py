"""Add assigned seating and real-time seat holds.

Revision ID: 20260817_0004
Revises: 20260816_0003
Create Date: 2026-08-17
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260817_0004"
down_revision: str | None = "20260816_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


seating_mode = postgresql.ENUM(
    "GENERAL_ADMISSION",
    "ASSIGNED",
    name="seating_mode",
    create_type=False,
)
seat_status = postgresql.ENUM(
    "AVAILABLE",
    "HELD",
    "SOLD",
    name="seat_status",
    create_type=False,
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
    seating_mode.create(op.get_bind(), checkfirst=True)
    seat_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "events",
        sa.Column(
            "seating_mode",
            seating_mode,
            server_default="GENERAL_ADMISSION",
            nullable=False,
        ),
    )

    op.create_table(
        "seat_maps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_label", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_seat_maps_event_id_events",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_seat_maps"),
        sa.UniqueConstraint("event_id", name="uq_seat_maps_event_id"),
    )
    op.create_table(
        "seat_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seat_map_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("seats_per_row", sa.Integer(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("position >= 0", name="position_non_negative"),
        sa.CheckConstraint("row_count > 0", name="row_count_positive"),
        sa.CheckConstraint("seats_per_row > 0", name="seats_per_row_positive"),
        sa.ForeignKeyConstraint(
            ["seat_map_id"],
            ["seat_maps.id"],
            name="fk_seat_sections_seat_map_id_seat_maps",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_seat_sections"),
        sa.UniqueConstraint(
            "seat_map_id", "name", name="uq_seat_sections_map_name"
        ),
        sa.UniqueConstraint(
            "seat_map_id", "position", name="uq_seat_sections_map_position"
        ),
    )
    op.create_index(
        "ix_seat_sections_seat_map_id", "seat_sections", ["seat_map_id"]
    )
    op.create_table(
        "event_seats",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_label", sa.String(length=4), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", seat_status, nullable=False),
        sa.Column(
            "active_reservation_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        *timestamps(),
        sa.CheckConstraint("number > 0", name="number_positive"),
        sa.CheckConstraint("position >= 0", name="position_non_negative"),
        sa.CheckConstraint(
            "(status = 'AVAILABLE' AND active_reservation_id IS NULL) OR "
            "(status IN ('HELD', 'SOLD') AND active_reservation_id IS NOT NULL)",
            name="status_matches_active_reservation",
        ),
        sa.ForeignKeyConstraint(
            ["active_reservation_id"],
            ["reservations.id"],
            name="fk_event_seats_active_reservation_id_reservations",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_event_seats_event_id_events",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["seat_sections.id"],
            name="fk_event_seats_section_id_seat_sections",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_event_seats"),
        sa.UniqueConstraint(
            "section_id", "row_label", "number", name="uq_event_seats_place"
        ),
    )
    op.create_index(
        "ix_event_seats_active_reservation_id",
        "event_seats",
        ["active_reservation_id"],
    )
    op.create_index("ix_event_seats_event_id", "event_seats", ["event_id"])
    op.create_index(
        "ix_event_seats_event_status", "event_seats", ["event_id", "status"]
    )
    op.create_index("ix_event_seats_section_id", "event_seats", ["section_id"])

    op.create_table(
        "reservation_seats",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_reservation_seats_reservation_id_reservations",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seat_id"],
            ["event_seats.id"],
            name="fk_reservation_seats_seat_id_event_seats",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservation_seats"),
        sa.UniqueConstraint(
            "reservation_id",
            "seat_id",
            name="uq_reservation_seats_reservation_seat",
        ),
    )
    op.create_index(
        "ix_reservation_seats_reservation_id",
        "reservation_seats",
        ["reservation_id"],
    )
    op.create_index("ix_reservation_seats_seat_id", "reservation_seats", ["seat_id"])
    op.create_index(
        "uq_reservation_seats_active_seat",
        "reservation_seats",
        ["seat_id"],
        unique=True,
        postgresql_where=sa.text("released_at IS NULL"),
    )

    op.add_column(
        "tickets",
        sa.Column("seat_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_tickets_seat_id_event_seats",
        "tickets",
        "event_seats",
        ["seat_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_tickets_seat_id", "tickets", ["seat_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_seat_id", table_name="tickets")
    op.drop_constraint(
        "fk_tickets_seat_id_event_seats", "tickets", type_="foreignkey"
    )
    op.drop_column("tickets", "seat_id")
    op.drop_table("reservation_seats")
    op.drop_table("event_seats")
    op.drop_table("seat_sections")
    op.drop_table("seat_maps")
    op.drop_column("events", "seating_mode")
    seat_status.drop(op.get_bind(), checkfirst=True)
    seating_mode.drop(op.get_bind(), checkfirst=True)
