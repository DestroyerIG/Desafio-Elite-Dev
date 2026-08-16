from datetime import UTC, datetime
from hmac import compare_digest
from io import BytesIO
from secrets import token_urlsafe
from uuid import UUID

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_ticket_token, hash_opaque_token, hash_ticket_token
from app.models.ticket import Ticket, TicketShare
from app.models.user import User
from app.modules.tickets.repository import (
    add_ticket_share,
    get_customer_ticket,
    get_ticket_share_by_hash,
    list_customer_tickets,
)


async def list_tickets(session: AsyncSession, customer: User) -> list[Ticket]:
    return await list_customer_tickets(session, customer.id)


async def get_ticket(
    session: AsyncSession,
    customer: User,
    ticket_id: UUID,
) -> Ticket:
    ticket = await get_customer_ticket(session, ticket_id, customer.id)
    if ticket is None:
        raise AppError("TICKET_NOT_FOUND", "Ingresso não encontrado.", 404)
    return ticket


async def create_ticket_qr(
    session: AsyncSession,
    customer: User,
    ticket_id: UUID,
) -> bytes:
    ticket = await get_ticket(session, customer, ticket_id)
    return _render_ticket_qr(ticket)


async def share_ticket(
    session: AsyncSession,
    customer: User,
    ticket_id: UUID,
) -> tuple[TicketShare, str]:
    ticket = await get_ticket(session, customer, ticket_id)
    token = token_urlsafe(32)
    ticket_share = TicketShare(
        ticket_id=ticket.id,
        token_hash=hash_opaque_token(token),
    )
    await add_ticket_share(session, ticket_share)
    await session.commit()
    return ticket_share, token


async def get_shared_ticket(
    session: AsyncSession,
    token: str,
) -> Ticket:
    ticket_share = await get_ticket_share_by_hash(
        session,
        hash_opaque_token(token),
    )
    now = datetime.now(UTC)
    if (
        ticket_share is None
        or ticket_share.revoked_at is not None
        or (
            ticket_share.expires_at is not None
            and ticket_share.expires_at <= now
        )
    ):
        raise AppError(
            "SHARED_TICKET_NOT_FOUND",
            "Ingresso compartilhado não encontrado ou indisponível.",
            404,
        )
    return ticket_share.ticket


async def create_shared_ticket_qr(
    session: AsyncSession,
    token: str,
) -> bytes:
    ticket = await get_shared_ticket(session, token)
    return _render_ticket_qr(ticket)


def _render_ticket_qr(ticket: Ticket) -> bytes:
    token = create_ticket_token(ticket.id, ticket.event_id)
    if not compare_digest(hash_ticket_token(token), ticket.qr_token_hash):
        raise AppError(
            "INVALID_TICKET",
            "Não foi possível validar este ingresso.",
            409,
        )

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0B1220", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
