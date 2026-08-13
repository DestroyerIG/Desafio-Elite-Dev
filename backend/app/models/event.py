from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import EventStatus, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.ticket import Ticket, TicketValidation
    from app.models.user import User


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="capacity_positive"),
        CheckConstraint("available_tickets >= 0", name="available_tickets_non_negative"),
        CheckConstraint("available_tickets <= capacity", name="available_tickets_within_capacity"),
        CheckConstraint("ticket_price >= 0", name="ticket_price_non_negative"),
        UniqueConstraint(
            "organizer_id",
            "external_provider",
            "external_id",
            name="uq_events_organizer_external_event",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organizer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    external_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    venue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    venue_address: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_tickets: Mapped[int] = mapped_column(Integer, nullable=False)
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus, name="event_status", values_callable=enum_values),
        default=EventStatus.DRAFT,
        nullable=False,
    )

    organizer: Mapped["User"] = relationship(back_populates="organized_events")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="event")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event")
    validations: Mapped[list["TicketValidation"]] = relationship(back_populates="event")

