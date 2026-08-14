from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.integrations.ticketmaster.client import (
    TicketmasterClient,
    get_ticketmaster_client,
)
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.catalog.schemas import CatalogEvent
from app.modules.catalog.service import search_catalog


router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]
CatalogClient = Annotated[TicketmasterClient, Depends(get_ticketmaster_client)]


@router.get("/events", response_model=list[CatalogEvent])
async def search_events(
    client: CatalogClient,
    _organizer: Organizer,
    q: Annotated[str, Query(min_length=2, max_length=100)],
) -> list[CatalogEvent]:
    return await search_catalog(client, q)

