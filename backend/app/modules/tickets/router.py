from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.tickets.schemas import (
    SharedTicketResponse,
    TicketResponse,
    TicketShareResponse,
)
from app.modules.tickets.service import (
    create_shared_ticket_qr,
    create_ticket_qr,
    get_shared_ticket,
    get_ticket,
    list_tickets,
    share_ticket,
)


router = APIRouter(prefix="/api/v1", tags=["tickets"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.get(
    "/me/tickets",
    response_model=list[TicketResponse],
    response_model_exclude_defaults=True,
)
async def customer_tickets(
    session: DatabaseSession,
    customer: Customer,
) -> list[TicketResponse]:
    tickets = await list_tickets(session, customer)
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    response_model_exclude_defaults=True,
)
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


@router.post(
    "/tickets/{ticket_id}/share",
    response_model=TicketShareResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket_share(
    ticket_id: UUID,
    session: DatabaseSession,
    customer: Customer,
) -> TicketShareResponse:
    ticket_share, token = await share_ticket(session, customer, ticket_id)
    return TicketShareResponse(
        token=token,
        expires_at=ticket_share.expires_at,
        created_at=ticket_share.created_at,
    )


@router.get(
    "/shared-tickets/{token}",
    response_model=SharedTicketResponse,
    response_model_exclude_defaults=True,
)
async def shared_ticket_detail(
    token: str,
    session: DatabaseSession,
) -> SharedTicketResponse:
    ticket = await get_shared_ticket(session, token)
    return SharedTicketResponse.model_validate(ticket)


@router.get(
    "/shared-tickets/{token}/qr",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
async def shared_ticket_qr(
    token: str,
    session: DatabaseSession,
) -> Response:
    content = await create_shared_ticket_qr(session, token)
    return Response(
        content=content,
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )
