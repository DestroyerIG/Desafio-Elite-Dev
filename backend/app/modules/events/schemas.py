from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import EventStatus


class EventCreate(BaseModel):
    external_id: str = Field(
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    capacity: int = Field(gt=0, le=1_000_000)
    ticket_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    image_url: HttpUrl | None = None
    venue_name: str | None = Field(default=None, min_length=2, max_length=255)
    venue_address: str | None = Field(default=None, min_length=2, max_length=2_000)
    event_date: datetime | None = None
    capacity: int | None = Field(default=None, gt=0, le=1_000_000)
    ticket_price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    status: EventStatus | None = None

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "EventUpdate":
        nullable_fields = {"description", "image_url"}
        for field_name in self.model_fields_set - nullable_fields:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        if "event_date" in self.model_fields_set and self.event_date:
            if self.event_date.tzinfo is None or self.event_date.utcoffset() is None:
                raise ValueError("event_date must include a timezone")
        return self


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizer_id: UUID
    external_provider: str
    external_id: str
    title: str
    description: str | None
    image_url: str | None
    venue_name: str
    venue_address: str
    event_date: datetime
    capacity: int
    available_tickets: int
    ticket_price: Decimal
    status: EventStatus
    created_at: datetime
    updated_at: datetime
