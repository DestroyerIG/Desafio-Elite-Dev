from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.ticket import Ticket, TicketShare


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


async def get_refund_for_reservation(
    session: AsyncSession,
    reservation_id: UUID,
) -> Refund | None:
    return await session.scalar(
        select(Refund).where(Refund.reservation_id == reservation_id)
    )


async def add_refund(session: AsyncSession, refund: Refund) -> Refund:
    session.add(refund)
    await session.flush()
    await session.refresh(refund)
    return refund


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


async def list_tickets_for_reservation_for_update(
    session: AsyncSession,
    reservation_id: UUID,
) -> list[Ticket]:
    tickets = await session.scalars(
        select(Ticket)
        .where(Ticket.reservation_id == reservation_id)
        .order_by(Ticket.id)
        .with_for_update()
    )
    return list(tickets)


async def revoke_ticket_shares(
    session: AsyncSession,
    ticket_ids: list[UUID],
    revoked_at: datetime,
) -> None:
    if not ticket_ids:
        return
    await session.execute(
        update(TicketShare)
        .where(
            TicketShare.ticket_id.in_(ticket_ids),
            TicketShare.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )
