from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.reservations.schemas import (
    CustomerReservationResponse,
    ReservationCreate,
    ReservationResponse,
)
from app.modules.reservations.service import (
    cancel_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
)


router = APIRouter(prefix="/api/v1", tags=["reservations"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.get(
    "/me/reservations",
    response_model=list[CustomerReservationResponse],
)
async def customer_reservations(
    session: DatabaseSession,
    customer: Customer,
) -> list[CustomerReservationResponse]:
    reservations = await list_reservations(session, customer)
    return [
        CustomerReservationResponse.model_validate(reservation)
        for reservation in reservations
    ]


@router.post(
    "/events/{event_id}/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reserve_event(
    event_id: UUID,
    data: ReservationCreate,
    session: DatabaseSession,
    customer: Customer,
) -> ReservationResponse:
    reservation = await create_reservation(session, customer, event_id, data)
    return ReservationResponse.model_validate(reservation)


@router.get(
    "/reservations/{reservation_id}",
    response_model=ReservationResponse,
)
async def reservation_detail(
    reservation_id: UUID,
    session: DatabaseSession,
    customer: Customer,
) -> ReservationResponse:
    reservation = await get_reservation(session, customer, reservation_id)
    return ReservationResponse.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ReservationResponse,
)
async def cancel_customer_reservation(
    reservation_id: UUID,
    session: DatabaseSession,
    customer: Customer,
) -> ReservationResponse:
    reservation = await cancel_reservation(session, customer, reservation_id)
    return ReservationResponse.model_validate(reservation)
