from datetime import datetime

from pydantic import BaseModel, HttpUrl


class CatalogEvent(BaseModel):
    external_id: str
    title: str
    description: str | None = None
    image_url: HttpUrl | None = None
    venue_name: str
    venue_address: str
    event_date: datetime

