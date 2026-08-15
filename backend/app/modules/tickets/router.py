from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.tickets.schemas import TicketResponse
from app.modules.tickets.service import create_ticket_qr, get_ticket, list_tickets


router = APIRouter(prefix="/api/v1", tags=["tickets"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.get("/me/tickets", response_model=list[TicketResponse])
async def customer_tickets(
    session: DatabaseSession,
    customer: Customer,
) -> list[TicketResponse]:
    tickets = await list_tickets(session, customer)
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def ticket_detail(
    ticket_id: UUID,
    session: DatabaseSession,
    customer: Customer,
) -> TicketResponse:
    ticket = await get_ticket(session, customer, ticket_id)
    return TicketResponse.model_validate(ticket)


@router.get(
    "/tickets/{ticket_id}/qr",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
async def ticket_qr(
    ticket_id: UUID,
    session: DatabaseSession,
    customer: Customer,
) -> Response:
    content = await create_ticket_qr(session, customer, ticket_id)
    return Response(
        content=content,
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )
