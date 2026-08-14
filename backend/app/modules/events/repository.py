from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventStatus
from app.models.event import Event


async def list_published_events(session: AsyncSession) -> list[Event]:
    result = await session.scalars(
        select(Event)
        .where(Event.status == EventStatus.PUBLISHED)
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
        select(Event).where(
            Event.id == event_id,
            Event.organizer_id == organizer_id,
        )
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

