from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import EventStatus
from app.models.event import Event
from app.models.reservation import Reservation


async def get_published_event_for_update(
    session: AsyncSession, event_id: UUID
) -> Event | None:
    return await session.scalar(
        select(Event)
        .where(
            Event.id == event_id,
            Event.status == EventStatus.PUBLISHED,
        )
        .with_for_update()
    )


async def get_event_for_update(
    session: AsyncSession, event_id: UUID
) -> Event | None:
    return await session.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
    )


async def get_customer_reservation(
    session: AsyncSession,
    reservation_id: UUID,
    customer_id: UUID,
    *,
    for_update: bool = False,
) -> Reservation | None:
    query = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.customer_id == customer_id,
    )
    if for_update:
        query = query.with_for_update().execution_options(populate_existing=True)
    return await session.scalar(query)


async def list_customer_reservations(
    session: AsyncSession,
    customer_id: UUID,
) -> list[Reservation]:
    result = await session.scalars(
        select(Reservation)
        .where(Reservation.customer_id == customer_id)
        .options(selectinload(Reservation.event))
        .order_by(Reservation.created_at.desc(), Reservation.id)
    )
    return list(result)


async def add_reservation(
    session: AsyncSession, reservation: Reservation
) -> Reservation:
    session.add(reservation)
    await session.flush()
    await session.refresh(reservation)
    return reservation
