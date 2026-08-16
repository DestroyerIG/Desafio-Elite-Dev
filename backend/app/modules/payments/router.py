from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.payments.gateway import PaymentGateway, get_payment_gateway
from app.modules.payments.schemas import PaymentCreate, PaymentResponse, RefundResponse
from app.modules.payments.service import pay_reservation, refund_paid_reservation
from app.modules.reservations.schemas import ReservationResponse


router = APIRouter(prefix="/api/v1", tags=["payments"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]
Gateway = Annotated[PaymentGateway, Depends(get_payment_gateway)]


@router.post(
    "/reservations/{reservation_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    reservation_id: UUID,
    data: PaymentCreate,
    session: DatabaseSession,
    customer: Customer,
    gateway: Gateway,
) -> PaymentResponse:
    outcome = await pay_reservation(
        session,
        customer,
        reservation_id,
        data,
        gateway,
    )
    return PaymentResponse(
        id=outcome.payment.id,
        reservation_id=outcome.payment.reservation_id,
        amount=outcome.payment.amount,
        status=outcome.payment.status,
        provider=outcome.payment.provider,
        failure_reason=outcome.payment.failure_reason,
        tickets_created=outcome.tickets_created,
        ticket_ids=outcome.ticket_ids,
        created_at=outcome.payment.created_at,
        updated_at=outcome.payment.updated_at,
    )


@router.post(
    "/reservations/{reservation_id}/refunds",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_refund(
    reservation_id: UUID,
    session: DatabaseSession,
    customer: Customer,
    gateway: Gateway,
) -> RefundResponse:
    outcome = await refund_paid_reservation(
        session,
        customer,
        reservation_id,
        gateway,
    )
    return RefundResponse(
        id=outcome.refund.id,
        reservation_id=outcome.refund.reservation_id,
        payment_id=outcome.refund.payment_id,
        amount=outcome.refund.amount,
        status=outcome.refund.status,
        provider=outcome.refund.provider,
        failure_reason=outcome.refund.failure_reason,
        processed_at=outcome.refund.processed_at,
        tickets_refunded=outcome.tickets_refunded,
        reservation=ReservationResponse.model_validate(outcome.reservation),
        created_at=outcome.refund.created_at,
        updated_at=outcome.refund.updated_at,
    )
