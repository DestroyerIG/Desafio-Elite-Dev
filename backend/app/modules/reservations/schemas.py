from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReservationStatus


class ReservationCreate(BaseModel):
    quantity: int = Field(gt=0, le=1_000_000)


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    event_id: UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    status: ReservationStatus
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
