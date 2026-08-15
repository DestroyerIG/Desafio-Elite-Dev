from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.models.user import User
from app.modules.reservations.repository import (
    add_reservation,
    get_customer_reservation,
    get_event_for_update,
    get_published_event_for_update,
)
from app.modules.reservations.schemas import ReservationCreate


async def create_reservation(
    session: AsyncSession,
    customer: User,
    event_id: UUID,
    data: ReservationCreate,
) -> Reservation:
    try:
        event = await get_published_event_for_update(session, event_id)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)

        if event.available_tickets == 0:
            raise AppError(
                "EVENT_SOLD_OUT",
                "Os ingressos deste evento estão esgotados.",
                409,
            )
        if event.available_tickets < data.quantity:
            raise AppError(
                "INSUFFICIENT_TICKETS",
                "Não existem ingressos suficientes disponíveis.",
                409,
            )

        event.available_tickets -= data.quantity
        reservation = Reservation(
            customer_id=customer.id,
            event_id=event.id,
            quantity=data.quantity,
            unit_price=event.ticket_price,
            total_amount=event.ticket_price * data.quantity,
            status=ReservationStatus.PENDING,
            expires_at=None,
        )
        await add_reservation(session, reservation)
        await session.commit()
        await session.refresh(reservation)
        return reservation
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "RESERVATION_FAILED",
            "Não foi possível criar a reserva.",
            409,
        ) from exc


async def get_reservation(
    session: AsyncSession,
    customer: User,
    reservation_id: UUID,
) -> Reservation:
    reservation = await get_customer_reservation(
        session, reservation_id, customer.id
    )
    if reservation is None:
        raise AppError("RESERVATION_NOT_FOUND", "Reserva não encontrada.", 404)
    return reservation


async def cancel_reservation(
    session: AsyncSession,
    customer: User,
    reservation_id: UUID,
) -> Reservation:
    try:
        existing_reservation = await get_customer_reservation(
            session, reservation_id, customer.id
        )
        if existing_reservation is None:
            raise AppError(
                "RESERVATION_NOT_FOUND",
                "Reserva não encontrada.",
                404,
            )

        event = await get_event_for_update(session, existing_reservation.event_id)
        reservation = await get_customer_reservation(
            session,
            reservation_id,
            customer.id,
            for_update=True,
        )
        if event is None or reservation is None:
            raise AppError(
                "RESERVATION_NOT_FOUND",
                "Reserva não encontrada.",
                404,
            )

        if reservation.status == ReservationStatus.CANCELLED:
            await session.commit()
            return reservation
        if reservation.status != ReservationStatus.PENDING:
            raise AppError(
                "RESERVATION_CANNOT_BE_CANCELLED",
                "Esta reserva não pode mais ser cancelada.",
                409,
            )

        event.available_tickets += reservation.quantity
        reservation.status = ReservationStatus.CANCELLED
        await session.commit()
        await session.refresh(reservation)
        return reservation
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "RESERVATION_CANCELLATION_FAILED",
            "Não foi possível cancelar a reserva.",
            409,
        ) from exc
