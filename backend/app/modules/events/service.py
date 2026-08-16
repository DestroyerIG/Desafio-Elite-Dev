from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.integrations.ticketmaster.client import TicketmasterClient
from app.models.enums import EventStatus
from app.models.event import Event
from app.models.user import User
from app.modules.events.repository import (
    add_event,
    get_by_external_id,
    get_organizer_event,
    get_published_event,
    list_organizer_events,
    list_published_events,
)
from app.modules.events.schemas import EventCreate, EventUpdate, PublicEventFilters


async def get_public_events(
    session: AsyncSession, filters: PublicEventFilters
) -> list[Event]:
    return await list_published_events(
        session,
        query=filters.q,
        date_from=filters.date_from,
        date_to=filters.date_to,
        available_only=filters.available_only,
    )


async def get_public_event(session: AsyncSession, event_id: UUID) -> Event:
    event = await get_published_event(session, event_id)
    if event is None:
        raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
    return event


async def get_events_for_organizer(
    session: AsyncSession, organizer: User
) -> list[Event]:
    return await list_organizer_events(session, organizer.id)


async def publish_external_event(
    session: AsyncSession,
    organizer: User,
    data: EventCreate,
    catalog_client: TicketmasterClient,
) -> Event:
    if await get_by_external_id(session, organizer.id, data.external_id):
        raise AppError(
            "EVENT_ALREADY_PUBLISHED",
            "Este evento externo já foi publicado por você.",
            409,
        )

    external_event = await catalog_client.get_event(data.external_id)
    event = Event(
        organizer_id=organizer.id,
        external_provider="ticketmaster",
        external_id=external_event.external_id,
        title=external_event.title,
        description=external_event.description,
        image_url=str(external_event.image_url) if external_event.image_url else None,
        venue_name=external_event.venue_name,
        venue_address=external_event.venue_address,
        event_date=external_event.event_date,
        capacity=data.capacity,
        available_tickets=data.capacity,
        ticket_price=data.ticket_price,
        status=EventStatus.PUBLISHED,
    )
    try:
        await add_event(session, event)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "EVENT_ALREADY_PUBLISHED",
            "Este evento externo já foi publicado por você.",
            409,
        ) from exc
    return event


async def update_organizer_event(
    session: AsyncSession,
    organizer: User,
    event_id: UUID,
    data: EventUpdate,
) -> Event:
    event = await get_organizer_event(session, event_id, organizer.id)
    if event is None:
        raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)

    changes = data.model_dump(exclude_unset=True)
    if changes.get("image_url") is not None:
        changes["image_url"] = str(changes["image_url"])

    if new_capacity := changes.pop("capacity", None):
        reserved_tickets = event.capacity - event.available_tickets
        if new_capacity < reserved_tickets:
            raise AppError(
                "INVALID_EVENT_CAPACITY",
                "A capacidade não pode ser menor que a quantidade já reservada.",
                409,
            )
        event.capacity = new_capacity
        event.available_tickets = new_capacity - reserved_tickets

    for field, value in changes.items():
        setattr(event, field, value)

    await session.commit()
    await session.refresh(event)
    return event


async def delete_organizer_event(
    session: AsyncSession, organizer: User, event_id: UUID
) -> None:
    event = await get_organizer_event(session, event_id, organizer.id)
    if event is None:
        raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)

    try:
        await session.delete(event)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "EVENT_HAS_RESERVATIONS",
            "Eventos com reservas não podem ser removidos.",
            409,
        ) from exc
