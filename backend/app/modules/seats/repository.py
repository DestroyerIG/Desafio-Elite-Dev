from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.models.seat import EventSeat, ReservationSeat, SeatMap, SeatSection


SEAT_MAP_LOAD = selectinload(SeatMap.sections).selectinload(SeatSection.seats)
RESERVATION_SEATS_LOAD = selectinload(Reservation.seats).selectinload(
    EventSeat.section
)


async def get_event_seat_map(
    session: AsyncSession,
    event_id: UUID,
    *,
    for_update: bool = False,
) -> SeatMap | None:
    query = (
        select(SeatMap)
        .where(SeatMap.event_id == event_id)
        .options(SEAT_MAP_LOAD)
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()
    return await session.scalar(query)


async def count_event_reservations(session: AsyncSession, event_id: UUID) -> int:
    count = await session.scalar(
        select(func.count(Reservation.id)).where(Reservation.event_id == event_id)
    )
    return int(count or 0)


async def get_seats_for_update(
    session: AsyncSession,
    event_id: UUID,
    seat_ids: list[UUID],
) -> list[EventSeat]:
    seats = await session.scalars(
        select(EventSeat)
        .where(EventSeat.event_id == event_id, EventSeat.id.in_(seat_ids))
        .order_by(EventSeat.id)
        .with_for_update()
    )
    return list(seats)


async def get_active_reservation_seats_for_update(
    session: AsyncSession,
    reservation_id: UUID,
) -> list[EventSeat]:
    seats = await session.scalars(
        select(EventSeat)
        .where(EventSeat.active_reservation_id == reservation_id)
        .order_by(EventSeat.position, EventSeat.id)
        .with_for_update()
    )
    return list(seats)


async def get_active_assignments_for_update(
    session: AsyncSession,
    reservation_id: UUID,
) -> list[ReservationSeat]:
    assignments = await session.scalars(
        select(ReservationSeat)
        .where(
            ReservationSeat.reservation_id == reservation_id,
            ReservationSeat.released_at.is_(None),
        )
        .order_by(ReservationSeat.id)
        .with_for_update()
    )
    return list(assignments)


async def get_due_reservations_for_update(
    session: AsyncSession,
    event_id: UUID,
    now: datetime,
) -> list[Reservation]:
    reservations = await session.scalars(
        select(Reservation)
        .where(
            Reservation.event_id == event_id,
            Reservation.status == ReservationStatus.PENDING,
            Reservation.expires_at.is_not(None),
            Reservation.expires_at <= now,
        )
        .order_by(Reservation.id)
        .with_for_update()
    )
    return list(reservations)


async def list_events_with_due_holds(
    session: AsyncSession,
    now: datetime,
    *,
    limit: int = 100,
) -> list[UUID]:
    event_ids = await session.scalars(
        select(Reservation.event_id)
        .where(
            Reservation.status == ReservationStatus.PENDING,
            Reservation.expires_at.is_not(None),
            Reservation.expires_at <= now,
        )
        .distinct()
        .order_by(Reservation.event_id)
        .limit(limit)
    )
    return list(event_ids)
