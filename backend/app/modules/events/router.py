from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.session import get_db_session
from app.integrations.ticketmaster.client import (
    TicketmasterClient,
    get_ticketmaster_client,
)
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.events.schemas import (
    CustomEventCreate,
    EventCreate,
    EventResponse,
    EventUpdate,
    PublicEventFilters,
)
from app.modules.events.service import (
    create_custom_event,
    delete_organizer_event,
    get_events_for_organizer,
    get_public_event,
    get_public_events,
    publish_external_event,
    update_organizer_event,
)
from app.modules.events.uploads import delete_event_image, save_event_image


router = APIRouter(prefix="/api/v1/events", tags=["events"])
organizer_router = APIRouter(prefix="/api/v1/organizer", tags=["organizer"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]
CatalogClient = Annotated[TicketmasterClient, Depends(get_ticketmaster_client)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_public_event_filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    available_only: bool = False,
) -> PublicEventFilters:
    try:
        return PublicEventFilters(
            q=q,
            date_from=date_from,
            date_to=date_to,
            available_only=available_only,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


PublicFilters = Annotated[PublicEventFilters, Depends(get_public_event_filters)]


@router.get("", response_model=list[EventResponse])
async def list_events(
    session: DatabaseSession, filters: PublicFilters
) -> list[EventResponse]:
    events = await get_public_events(session, filters)
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
    settings: AppSettings,
) -> Response:
    image_url = await delete_organizer_event(session, organizer, event_id)
    await delete_event_image(image_url, settings)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@organizer_router.get("/events", response_model=list[EventResponse])
async def organizer_events(
    session: DatabaseSession, organizer: Organizer
) -> list[EventResponse]:
    events = await get_events_for_organizer(session, organizer)
    return [EventResponse.model_validate(event) for event in events]


@organizer_router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organizer_event(
    session: DatabaseSession,
    organizer: Organizer,
    settings: AppSettings,
    title: Annotated[str, Form()],
    venue_name: Annotated[str, Form()],
    venue_address: Annotated[str, Form()],
    event_date: Annotated[str, Form()],
    capacity: Annotated[str, Form()],
    ticket_price: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> EventResponse:
    try:
        data = CustomEventCreate.model_validate(
            {
                "title": title,
                "description": description,
                "venue_name": venue_name,
                "venue_address": venue_address,
                "event_date": event_date,
                "capacity": capacity,
                "ticket_price": ticket_price,
            }
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    image_url: str | None = None
    try:
        if image is not None:
            image_url = await save_event_image(image, settings)
        event = await create_custom_event(session, organizer, data, image_url)
    except Exception:
        await delete_event_image(image_url, settings)
        raise
    finally:
        if image is not None:
            await image.close()

    return EventResponse.model_validate(event)
