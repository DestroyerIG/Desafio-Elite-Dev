from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.models.ticket import Ticket


async def get_approved_payment(
    session: AsyncSession,
    reservation_id: UUID,
) -> Payment | None:
    return await session.scalar(
        select(Payment)
        .where(
            Payment.reservation_id == reservation_id,
            Payment.status == PaymentStatus.APPROVED,
        )
        .order_by(Payment.created_at.desc())
    )


async def add_payment(session: AsyncSession, payment: Payment) -> Payment:
    session.add(payment)
    await session.flush()
    await session.refresh(payment)
    return payment


async def add_tickets(session: AsyncSession, tickets: list[Ticket]) -> None:
    session.add_all(tickets)
    await session.flush()


async def list_ticket_ids_for_reservation(
    session: AsyncSession,
    reservation_id: UUID,
) -> list[UUID]:
    ticket_ids = await session.scalars(
        select(Ticket.id)
        .where(Ticket.reservation_id == reservation_id)
        .order_by(Ticket.id)
    )
    return list(ticket_ids)
