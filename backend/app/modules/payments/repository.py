from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.ticket import Ticket


async def get_payment_by_reservation(
    session: AsyncSession,
    reservation_id: UUID,
) -> Payment | None:
    return await session.scalar(
        select(Payment).where(Payment.reservation_id == reservation_id)
    )


async def add_payment(session: AsyncSession, payment: Payment) -> Payment:
    session.add(payment)
    await session.flush()
    await session.refresh(payment)
    return payment


async def add_tickets(session: AsyncSession, tickets: list[Ticket]) -> None:
    session.add_all(tickets)
    await session.flush()


async def count_tickets_for_reservation(
    session: AsyncSession,
    reservation_id: UUID,
) -> int:
    count = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.reservation_id == reservation_id)
    )
    return int(count or 0)
