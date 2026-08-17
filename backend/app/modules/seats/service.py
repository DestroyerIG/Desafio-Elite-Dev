from datetime import UTC, datetime, timedelta
import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.enums import ReservationStatus, SeatStatus, SeatingMode
from app.models.reservation import Reservation
from app.models.seat import EventSeat, ReservationSeat, SeatMap, SeatSection
from app.models.user import User
from app.modules.events.repository import get_organizer_event
from app.modules.reservations.repository import (
    add_reservation,
    get_customer_reservation,
    get_event_for_update,
    get_published_event_for_update,
)
from app.modules.seats.repository import (
    count_event_reservations,
    get_active_assignments_for_update,
    get_active_reservation_seats_for_update,
    get_due_reservations_for_update,
    get_event_seat_map,
    get_seats_for_update,
    list_events_with_due_holds,
)
from app.modules.seats.schemas import SeatHoldCreate, SeatMapConfigure


SEAT_HOLD_DURATION = timedelta(minutes=10)


def _row_label(index: int) -> str:
    label = ""
    value = index + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        label = chr(65 + remainder) + label
    return label


async def notify_seat_map_changed(
    session: AsyncSession, event_id: UUID, version: int
) -> None:
    payload = json.dumps(
        {"event_id": str(event_id), "version": version}, separators=(",", ":")
    )
    await session.execute(
        text("SELECT pg_notify('seat_map_updates', :payload)"),
        {"payload": payload},
    )


async def configure_seat_map(
    session: AsyncSession,
    organizer: User,
    event_id: UUID,
    data: SeatMapConfigure,
) -> SeatMap:
    try:
        event = await get_organizer_event(session, event_id, organizer.id)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
        if await count_event_reservations(session, event.id):
            raise AppError(
                "SEAT_MAP_LOCKED",
                "O mapa não pode ser alterado depois da primeira reserva.",
                409,
            )

        total_seats = sum(
            section.row_count * section.seats_per_row for section in data.sections
        )
        if total_seats != event.capacity:
            raise AppError(
                "SEAT_MAP_CAPACITY_MISMATCH",
                f"O mapa deve possuir exatamente {event.capacity} assentos.",
                409,
            )

        existing_map = await get_event_seat_map(session, event.id, for_update=True)
        if existing_map is not None:
            await session.delete(existing_map)
            await session.flush()

        seat_map = SeatMap(
            event_id=event.id,
            stage_label=data.stage_label,
            version=1,
        )
        session.add(seat_map)
        await session.flush()

        global_position = 0
        for section_position, section_data in enumerate(data.sections):
            section = SeatSection(
                seat_map_id=seat_map.id,
                name=section_data.name,
                position=section_position,
                row_count=section_data.row_count,
                seats_per_row=section_data.seats_per_row,
            )
            session.add(section)
            await session.flush()
            seats: list[EventSeat] = []
            for row_index in range(section_data.row_count):
                row_label = _row_label(row_index)
                for seat_number in range(1, section_data.seats_per_row + 1):
                    seats.append(
                        EventSeat(
                            event_id=event.id,
                            section_id=section.id,
                            row_label=row_label,
                            number=seat_number,
                            label=f"{row_label}{seat_number}",
                            position=global_position,
                            status=SeatStatus.AVAILABLE,
                        )
                    )
                    global_position += 1
            session.add_all(seats)

        event.seating_mode = SeatingMode.ASSIGNED
        event.available_tickets = event.capacity
        await notify_seat_map_changed(session, event.id, seat_map.version)
        await session.commit()
        configured_map = await get_event_seat_map(session, event.id)
        if configured_map is None:
            raise AppError(
                "SEAT_MAP_CONFIGURATION_FAILED",
                "Não foi possível carregar o mapa configurado.",
                409,
            )
        return configured_map
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "SEAT_MAP_CONFIGURATION_FAILED",
            "Não foi possível configurar o mapa de assentos.",
            409,
        ) from exc


async def remove_seat_map(
    session: AsyncSession,
    organizer: User,
    event_id: UUID,
) -> None:
    try:
        event = await get_organizer_event(session, event_id, organizer.id)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
        if await count_event_reservations(session, event.id):
            raise AppError(
                "SEAT_MAP_LOCKED",
                "O mapa não pode ser removido depois da primeira reserva.",
                409,
            )
        seat_map = await get_event_seat_map(session, event.id, for_update=True)
        if seat_map is None:
            event.seating_mode = SeatingMode.GENERAL_ADMISSION
            await session.commit()
            return

        await session.delete(seat_map)
        event.seating_mode = SeatingMode.GENERAL_ADMISSION
        event.available_tickets = event.capacity
        await notify_seat_map_changed(session, event.id, seat_map.version + 1)
        await session.commit()
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "SEAT_MAP_REMOVAL_FAILED",
            "Não foi possível remover o mapa de assentos.",
            409,
        ) from exc


async def get_organizer_seat_map(
    session: AsyncSession,
    organizer: User,
    event_id: UUID,
) -> SeatMap:
    event = await get_organizer_event(session, event_id, organizer.id)
    if event is None:
        raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
    seat_map = await get_event_seat_map(session, event.id)
    if seat_map is None:
        raise AppError(
            "SEAT_MAP_NOT_CONFIGURED",
            "O mapa de assentos deste evento não está configurado.",
            404,
        )
    return seat_map


async def _release_reservation_seats(
    session: AsyncSession,
    reservation: Reservation,
    released_at: datetime,
    seat_map: SeatMap,
) -> int:
    seats = await get_active_reservation_seats_for_update(session, reservation.id)
    assignments = await get_active_assignments_for_update(session, reservation.id)
    if len(seats) != reservation.quantity or len(assignments) != reservation.quantity:
        raise AppError(
            "SEAT_HOLD_STATE_INVALID",
            "Os assentos ativos não correspondem à reserva.",
            409,
        )
    for seat in seats:
        seat.status = SeatStatus.AVAILABLE
        seat.active_reservation_id = None
    for assignment in assignments:
        assignment.released_at = released_at
    seat_map.version += 1
    return len(seats)


async def release_reservation_seats(
    session: AsyncSession,
    reservation: Reservation,
    released_at: datetime,
) -> int | None:
    seat_map = await get_event_seat_map(
        session, reservation.event_id, for_update=True
    )
    if seat_map is None:
        return None
    await _release_reservation_seats(session, reservation, released_at, seat_map)
    return seat_map.version


async def mark_reservation_seats_sold(
    session: AsyncSession,
    reservation: Reservation,
) -> tuple[list[EventSeat], int | None]:
    seat_map = await get_event_seat_map(
        session, reservation.event_id, for_update=True
    )
    if seat_map is None:
        return [], None
    seats = await get_active_reservation_seats_for_update(session, reservation.id)
    if (
        len(seats) != reservation.quantity
        or any(seat.status != SeatStatus.HELD for seat in seats)
    ):
        raise AppError(
            "SEAT_HOLD_STATE_INVALID",
            "Os assentos reservados não estão disponíveis para pagamento.",
            409,
        )
    for seat in seats:
        seat.status = SeatStatus.SOLD
    seat_map.version += 1
    return seats, seat_map.version


async def _expire_due_holds_with_locked_event(
    session: AsyncSession,
    event_id: UUID,
    now: datetime,
) -> tuple[int, int | None]:
    reservations = await get_due_reservations_for_update(session, event_id, now)
    if not reservations:
        return 0, None
    seat_map = await get_event_seat_map(session, event_id, for_update=True)
    if seat_map is None:
        raise AppError(
            "SEAT_MAP_NOT_CONFIGURED",
            "O mapa de assentos deste evento não está configurado.",
            409,
        )

    released = 0
    for reservation in reservations:
        released += await _release_reservation_seats(
            session, reservation, now, seat_map
        )
        reservation.status = ReservationStatus.EXPIRED
    return released, seat_map.version


async def expire_due_holds_for_event(
    session: AsyncSession,
    event_id: UUID,
) -> int:
    event = await get_event_for_update(session, event_id)
    if event is None:
        await session.rollback()
        return 0
    released, version = await _expire_due_holds_with_locked_event(
        session, event.id, datetime.now(UTC)
    )
    if not released:
        await session.rollback()
        return 0
    event.available_tickets += released
    if version is not None:
        await notify_seat_map_changed(session, event.id, version)
    await session.commit()
    return released


async def expire_due_holds_batch(session: AsyncSession) -> int:
    event_ids = await list_events_with_due_holds(session, datetime.now(UTC))
    await session.rollback()
    released = 0
    for event_id in event_ids:
        released += await expire_due_holds_for_event(session, event_id)
    return released


async def get_public_seat_map(session: AsyncSession, event_id: UUID) -> SeatMap:
    event = await get_published_event_for_update(session, event_id)
    if event is None:
        await session.rollback()
        raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
    if event.seating_mode != SeatingMode.ASSIGNED:
        await session.rollback()
        raise AppError(
            "SEAT_MAP_NOT_CONFIGURED",
            "Este evento não utiliza assentos marcados.",
            404,
        )
    released, version = await _expire_due_holds_with_locked_event(
        session, event.id, datetime.now(UTC)
    )
    if released:
        event.available_tickets += released
        if version is not None:
            await notify_seat_map_changed(session, event.id, version)
        await session.commit()
    else:
        await session.rollback()

    seat_map = await get_event_seat_map(session, event_id)
    if seat_map is None:
        raise AppError(
            "SEAT_MAP_NOT_CONFIGURED",
            "O mapa de assentos deste evento não está configurado.",
            404,
        )
    return seat_map


async def create_seat_hold(
    session: AsyncSession,
    customer: User,
    event_id: UUID,
    data: SeatHoldCreate,
) -> Reservation:
    try:
        event = await get_published_event_for_update(session, event_id)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)
        if event.seating_mode != SeatingMode.ASSIGNED:
            raise AppError(
                "SEAT_MAP_NOT_CONFIGURED",
                "Este evento não utiliza assentos marcados.",
                409,
            )

        now = datetime.now(UTC)
        released, current_version = await _expire_due_holds_with_locked_event(
            session, event.id, now
        )
        event.available_tickets += released
        seat_map = await get_event_seat_map(session, event.id, for_update=True)
        if seat_map is None:
            raise AppError(
                "SEAT_MAP_NOT_CONFIGURED",
                "O mapa de assentos deste evento não está configurado.",
                409,
            )
        seats = await get_seats_for_update(session, event.id, data.seat_ids)
        if len(seats) != len(data.seat_ids):
            raise AppError(
                "SEAT_NOT_FOUND",
                "Um ou mais assentos não pertencem a este evento.",
                404,
            )
        if any(seat.status != SeatStatus.AVAILABLE for seat in seats):
            raise AppError(
                "SEATS_UNAVAILABLE",
                "Um ou mais assentos acabaram de ficar indisponíveis. Atualize sua seleção.",
                409,
            )
        if event.available_tickets < len(seats):
            raise AppError(
                "INSUFFICIENT_TICKETS",
                "Não existem assentos suficientes disponíveis.",
                409,
            )

        reservation = Reservation(
            customer_id=customer.id,
            event_id=event.id,
            quantity=len(seats),
            unit_price=event.ticket_price,
            total_amount=event.ticket_price * len(seats),
            status=ReservationStatus.PENDING,
            expires_at=now + SEAT_HOLD_DURATION,
        )
        await add_reservation(session, reservation)
        for seat in seats:
            seat.status = SeatStatus.HELD
            seat.active_reservation_id = reservation.id
            session.add(
                ReservationSeat(reservation_id=reservation.id, seat_id=seat.id)
            )
        event.available_tickets -= len(seats)
        seat_map.version = max(seat_map.version, current_version or 0) + 1
        await notify_seat_map_changed(session, event.id, seat_map.version)
        await session.commit()

        loaded = await get_customer_reservation(
            session, reservation.id, customer.id
        )
        if loaded is None:
            raise AppError(
                "RESERVATION_FAILED", "Não foi possível carregar a reserva.", 409
            )
        return loaded
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "SEATS_UNAVAILABLE",
            "Um ou mais assentos acabaram de ficar indisponíveis. Atualize sua seleção.",
            409,
        ) from exc
