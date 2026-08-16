from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.ticket import Ticket, TicketValidation


async def get_event(
    session: AsyncSession,
    event_id: UUID,
) -> Event | None:
    return await session.get(Event, event_id)


async def get_ticket_by_id_for_update(
    session: AsyncSession,
    ticket_id: UUID,
) -> Ticket | None:
    return await session.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def get_ticket_by_public_code_for_update(
    session: AsyncSession,
    public_code: str,
) -> Ticket | None:
    return await session.scalar(
        select(Ticket)
        .where(Ticket.public_code == public_code)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def add_ticket_validation(
    session: AsyncSession,
    validation: TicketValidation,
) -> TicketValidation:
    session.add(validation)
    await session.flush()
    await session.refresh(validation)
    return validation
