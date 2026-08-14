from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.integrations.ticketmaster.client import (
    TicketmasterClient,
    get_ticketmaster_client,
)
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.events.schemas import EventCreate, EventResponse, EventUpdate
from app.modules.events.service import (
    delete_organizer_event,
    get_events_for_organizer,
    get_public_event,
    get_public_events,
    publish_external_event,
    update_organizer_event,
)


router = APIRouter(prefix="/api/v1/events", tags=["events"])
organizer_router = APIRouter(prefix="/api/v1/organizer", tags=["organizer"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]
CatalogClient = Annotated[TicketmasterClient, Depends(get_ticketmaster_client)]


@router.get("", response_model=list[EventResponse])
async def list_events(session: DatabaseSession) -> list[EventResponse]:
    events = await get_public_events(session)
    return [EventResponse.model_validate(event) for event in events]


@router.get("/{event_id}", response_model=EventResponse)
async def event_detail(event_id: UUID, session: DatabaseSession) -> EventResponse:
    return EventResponse.model_validate(await get_public_event(session, event_id))


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    session: DatabaseSession,
    organizer: Organizer,
    catalog_client: CatalogClient,
) -> EventResponse:
    event = await publish_external_event(session, organizer, data, catalog_client)
    return EventResponse.model_validate(event)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    session: DatabaseSession,
    organizer: Organizer,
) -> EventResponse:
    event = await update_organizer_event(session, organizer, event_id, data)
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    session: DatabaseSession,
    organizer: Organizer,
) -> Response:
    await delete_organizer_event(session, organizer, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@organizer_router.get("/events", response_model=list[EventResponse])
async def organizer_events(
    session: DatabaseSession, organizer: Organizer
) -> list[EventResponse]:
    events = await get_events_for_organizer(session, organizer)
    return [EventResponse.model_validate(event) for event in events]

