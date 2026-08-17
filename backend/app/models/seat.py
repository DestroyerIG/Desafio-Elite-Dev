from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import SeatStatus, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.reservation import Reservation
    from app.models.ticket import Ticket


class SeatMap(TimestampMixin, Base):
    __tablename__ = "seat_maps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    stage_label: Mapped[str] = mapped_column(String(80), default="Palco", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    event: Mapped["Event"] = relationship(back_populates="seat_map")
    sections: Mapped[list["SeatSection"]] = relationship(
        back_populates="seat_map",
        cascade="all, delete-orphan",
        order_by="SeatSection.position",
    )


class SeatSection(TimestampMixin, Base):
    __tablename__ = "seat_sections"
    __table_args__ = (
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint("row_count > 0", name="row_count_positive"),
        CheckConstraint("seats_per_row > 0", name="seats_per_row_positive"),
        UniqueConstraint("seat_map_id", "name", name="uq_seat_sections_map_name"),
        UniqueConstraint(
            "seat_map_id", "position", name="uq_seat_sections_map_position"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    seat_map_id: Mapped[UUID] = mapped_column(
        ForeignKey("seat_maps.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_per_row: Mapped[int] = mapped_column(Integer, nullable=False)

    seat_map: Mapped["SeatMap"] = relationship(back_populates="sections")
    seats: Mapped[list["EventSeat"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="EventSeat.position",
    )


class EventSeat(TimestampMixin, Base):
    __tablename__ = "event_seats"
    __table_args__ = (
        CheckConstraint("number > 0", name="number_positive"),
        CheckConstraint("position >= 0", name="position_non_negative"),
        CheckConstraint(
            "(status = 'AVAILABLE' AND active_reservation_id IS NULL) OR "
            "(status IN ('HELD', 'SOLD') AND active_reservation_id IS NOT NULL)",
            name="status_matches_active_reservation",
        ),
        UniqueConstraint(
            "section_id", "row_label", "number", name="uq_event_seats_place"
        ),
        Index("ix_event_seats_event_status", "event_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    section_id: Mapped[UUID] = mapped_column(
        ForeignKey("seat_sections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    row_label: Mapped[str] = mapped_column(String(4), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SeatStatus] = mapped_column(
        SAEnum(SeatStatus, name="seat_status", values_callable=enum_values),
        default=SeatStatus.AVAILABLE,
        nullable=False,
    )
    active_reservation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), index=True
    )

    event: Mapped["Event"] = relationship(back_populates="seats")
    section: Mapped["SeatSection"] = relationship(back_populates="seats")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="seat")


class ReservationSeat(TimestampMixin, Base):
    __tablename__ = "reservation_seats"
    __table_args__ = (
        UniqueConstraint(
            "reservation_id", "seat_id", name="uq_reservation_seats_reservation_seat"
        ),
        Index(
            "uq_reservation_seats_active_seat",
            "seat_id",
            unique=True,
            postgresql_where=text("released_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reservation_id: Mapped[UUID] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    seat_id: Mapped[UUID] = mapped_column(
        ForeignKey("event_seats.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reservation: Mapped["Reservation"] = relationship(
        back_populates="seat_assignments"
    )
    seat: Mapped["EventSeat"] = relationship()
