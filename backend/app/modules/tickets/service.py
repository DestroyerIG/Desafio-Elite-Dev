from hmac import compare_digest
from io import BytesIO
from uuid import UUID

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_ticket_token, hash_ticket_token
from app.models.ticket import Ticket
from app.models.user import User
from app.modules.tickets.repository import (
    get_customer_ticket,
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
