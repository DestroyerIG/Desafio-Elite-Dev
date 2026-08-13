from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import UserRole, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.reservation import Reservation
    from app.models.ticket import Ticket, TicketValidation


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=enum_values), nullable=False
    )

    organized_events: Mapped[list["Event"]] = relationship(back_populates="organizer")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="customer")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="owner")
    validations: Mapped[list["TicketValidation"]] = relationship(back_populates="gate_user")
