from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import TicketStatus
from app.modules.reservations.schemas import ReservationSeatResponse


class TicketEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    image_url: str | None
    venue_name: str
    venue_address: str
    event_date: datetime


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reservation_id: UUID
    event_id: UUID
    public_code: str
    status: TicketStatus
    used_at: datetime | None
    created_at: datetime
    event: TicketEventResponse
    seat: ReservationSeatResponse | None = None


class TicketShareResponse(BaseModel):
    token: str
    expires_at: datetime | None
    created_at: datetime


class SharedTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_code: str
    status: TicketStatus
    used_at: datetime | None
    event: TicketEventResponse
    seat: ReservationSeatResponse | None = None
