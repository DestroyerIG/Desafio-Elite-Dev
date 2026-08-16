from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventStatus
from app.models.event import Event


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_published_events(
    session: AsyncSession,
    *,
    query: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    available_only: bool = False,
) -> list[Event]:
    conditions = [Event.status == EventStatus.PUBLISHED]

    if query:
        pattern = f"%{_escape_like(query)}%"
        conditions.append(
            or_(
                Event.title.ilike(pattern, escape="\\"),
                Event.venue_name.ilike(pattern, escape="\\"),
                Event.venue_address.ilike(pattern, escape="\\"),
            )
        )
    if date_from is not None:
        conditions.append(Event.event_date >= date_from)
    if date_to is not None:
        conditions.append(Event.event_date <= date_to)
    if available_only:
        conditions.append(Event.available_tickets > 0)

    result = await session.scalars(
        select(Event)
        .where(*conditions)
        .order_by(Event.event_date.asc())
    )
    return list(result.all())


async def get_published_event(
    session: AsyncSession, event_id: UUID
) -> Event | None:
    return await session.scalar(
        select(Event).where(
            Event.id == event_id,
            Event.status == EventStatus.PUBLISHED,
        )
    )


async def list_organizer_events(
    session: AsyncSession, organizer_id: UUID
) -> list[Event]:
    result = await session.scalars(
        select(Event)
        .where(Event.organizer_id == organizer_id)
        .order_by(Event.created_at.desc())
    )
    return list(result.all())


async def get_organizer_event(
    session: AsyncSession, event_id: UUID, organizer_id: UUID
) -> Event | None:
    return await session.scalar(
        select(Event)
        .where(
            Event.id == event_id,
            Event.organizer_id == organizer_id,
        )
        .with_for_update()
    )


async def get_by_external_id(
    session: AsyncSession, organizer_id: UUID, external_id: str
) -> Event | None:
    return await session.scalar(
        select(Event).where(
            Event.organizer_id == organizer_id,
            Event.external_provider == "ticketmaster",
            Event.external_id == external_id,
        )
    )


async def add_event(session: AsyncSession, event: Event) -> Event:
    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event
