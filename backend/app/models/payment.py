from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import PaymentStatus, enum_values
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount >= 0", name="amount_non_negative"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reservation_id: Mapped[UUID] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", values_callable=enum_values), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)

    reservation: Mapped["Reservation"] = relationship(back_populates="payments")
