from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.seat import EventSeat
from app.models.ticket import Ticket, TicketShare


TICKET_SEAT_LOAD = selectinload(Ticket.seat).selectinload(EventSeat.section)


async def list_customer_tickets(
    session: AsyncSession,
    customer_id: UUID,
) -> list[Ticket]:
    result = await session.scalars(
        select(Ticket)
        .where(Ticket.owner_id == customer_id)
        .options(selectinload(Ticket.event))
        .options(TICKET_SEAT_LOAD)
        .order_by(Ticket.created_at.desc(), Ticket.id)
    )
    return list(result)


async def get_customer_ticket(
    session: AsyncSession,
    ticket_id: UUID,
    customer_id: UUID,
) -> Ticket | None:
    return await session.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id, Ticket.owner_id == customer_id)
        .options(selectinload(Ticket.event))
        .options(TICKET_SEAT_LOAD)
    )


async def get_customer_ticket_for_update(
    session: AsyncSession,
    ticket_id: UUID,
    customer_id: UUID,
) -> Ticket | None:
    return await session.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id, Ticket.owner_id == customer_id)
        .options(selectinload(Ticket.event))
        .options(TICKET_SEAT_LOAD)
        .with_for_update()
    )


async def add_ticket_share(
    session: AsyncSession,
    ticket_share: TicketShare,
) -> TicketShare:
    session.add(ticket_share)
    await session.flush()
    await session.refresh(ticket_share)
    return ticket_share


async def get_ticket_share_by_hash(
    session: AsyncSession,
    token_hash: str,
) -> TicketShare | None:
    return await session.scalar(
        select(TicketShare)
        .where(TicketShare.token_hash == token_hash)
        .options(selectinload(TicketShare.ticket).selectinload(Ticket.event))
        .options(selectinload(TicketShare.ticket).options(TICKET_SEAT_LOAD))
    )
