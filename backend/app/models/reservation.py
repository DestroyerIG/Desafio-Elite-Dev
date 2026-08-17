from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ReservationStatus, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.payment import Payment
    from app.models.refund import Refund
    from app.models.seat import EventSeat, ReservationSeat
    from app.models.ticket import Ticket
    from app.models.user import User


class Reservation(TimestampMixin, Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
        CheckConstraint("total_amount = quantity * unit_price", name="total_matches_quantity"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        SAEnum(ReservationStatus, name="reservation_status", values_callable=enum_values),
        default=ReservationStatus.PENDING,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped["User"] = relationship(back_populates="reservations")
    event: Mapped["Event"] = relationship(back_populates="reservations")
    payments: Mapped[list["Payment"]] = relationship(back_populates="reservation")
    refund: Mapped["Refund | None"] = relationship(
        back_populates="reservation", uselist=False
    )
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="reservation")
    seat_assignments: Mapped[list["ReservationSeat"]] = relationship(
        back_populates="reservation",
        order_by="ReservationSeat.created_at",
    )
    seats: Mapped[list["EventSeat"]] = relationship(
        secondary="reservation_seats",
        viewonly=True,
        order_by="EventSeat.position",
    )
