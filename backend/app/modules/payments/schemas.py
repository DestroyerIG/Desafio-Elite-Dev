from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PaymentStatus, RefundStatus
from app.modules.reservations.schemas import ReservationResponse


class PaymentCreate(BaseModel):
    card_number: str = Field(min_length=13, max_length=23)

    @field_validator("card_number")
    @classmethod
    def normalize_card_number(cls, value: str) -> str:
        normalized = value.replace(" ", "").replace("-", "")
        if not normalized.isdigit() or not 13 <= len(normalized) <= 19:
            raise ValueError("O número do cartão deve conter entre 13 e 19 dígitos.")
        return normalized


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reservation_id: UUID
    amount: Decimal
    status: PaymentStatus
    provider: str
    failure_reason: str | None
    tickets_created: int
    ticket_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class RefundResponse(BaseModel):
    id: UUID
    reservation_id: UUID
    payment_id: UUID
    amount: Decimal
    status: RefundStatus
    provider: str
    failure_reason: str | None
    processed_at: datetime | None
    tickets_refunded: int
    reservation: ReservationResponse
    created_at: datetime
    updated_at: datetime
