from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import TicketStatus, ValidationResult, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.reservation import Reservation
    from app.models.seat import EventSeat
    from app.models.user import User


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            "(status = 'USED' AND used_at IS NOT NULL) OR (status <> 'USED' AND used_at IS NULL)",
            name="used_at_matches_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reservation_id: Mapped[UUID] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    seat_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("event_seats.id", ondelete="RESTRICT"), index=True
    )
    public_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    qr_token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus, name="ticket_status", values_callable=enum_values),
        default=TicketStatus.ACTIVE,
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reservation: Mapped["Reservation"] = relationship(back_populates="tickets")
    event: Mapped["Event"] = relationship(back_populates="tickets")
    owner: Mapped["User"] = relationship(back_populates="tickets")
    seat: Mapped["EventSeat | None"] = relationship(back_populates="tickets")
    shares: Mapped[list["TicketShare"]] = relationship(back_populates="ticket")
    validations: Mapped[list["TicketValidation"]] = relationship(back_populates="ticket")


class TicketShare(TimestampMixin, Base):
    __tablename__ = "ticket_shares"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ticket: Mapped["Ticket"] = relationship(back_populates="shares")


class TicketValidation(Base):
    __tablename__ = "ticket_validations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="SET NULL"), index=True
    )
    gate_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    result: Mapped[ValidationResult] = mapped_column(
        SAEnum(ValidationResult, name="validation_result", values_callable=enum_values), nullable=False
    )
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket: Mapped["Ticket | None"] = relationship(back_populates="validations")
    gate_user: Mapped["User"] = relationship(back_populates="validations")
    event: Mapped["Event"] = relationship(back_populates="validations")
