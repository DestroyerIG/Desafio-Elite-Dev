from dataclasses import dataclass
from secrets import token_hex
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_ticket_token, hash_ticket_token
from app.models.enums import PaymentStatus, ReservationStatus, TicketStatus
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.models.user import User
from app.modules.payments.gateway import PaymentGateway
from app.modules.payments.repository import (
    add_payment,
    add_tickets,
    count_tickets_for_reservation,
    get_payment_by_reservation,
)
from app.modules.payments.schemas import PaymentCreate
from app.modules.reservations.repository import get_customer_reservation


@dataclass(frozen=True, slots=True)
class PaymentOutcome:
    payment: Payment
    tickets_created: int


def _new_public_code() -> str:
    code = token_hex(6).upper()
    return f"ELT-{code[:4]}-{code[4:8]}-{code[8:]}"


def _build_tickets(
    *,
    reservation_id: UUID,
    event_id: UUID,
    owner_id: UUID,
    quantity: int,
) -> list[Ticket]:
    tickets: list[Ticket] = []
    for _ in range(quantity):
        ticket_id = uuid4()
        token = create_ticket_token(ticket_id, event_id)
        tickets.append(
            Ticket(
                id=ticket_id,
                reservation_id=reservation_id,
                event_id=event_id,
                owner_id=owner_id,
                public_code=_new_public_code(),
                qr_token_hash=hash_ticket_token(token),
                status=TicketStatus.ACTIVE,
            )
        )
    return tickets


async def pay_reservation(
    session: AsyncSession,
    customer: User,
    reservation_id: UUID,
    data: PaymentCreate,
    gateway: PaymentGateway,
) -> PaymentOutcome:
    try:
        reservation = await get_customer_reservation(
            session,
            reservation_id,
            customer.id,
            for_update=True,
        )
        if reservation is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reserva não encontrada.", 404)

        existing_payment = await get_payment_by_reservation(session, reservation.id)
        if existing_payment is not None:
            tickets_created = await count_tickets_for_reservation(
                session, reservation.id
            )
            if existing_payment.status == PaymentStatus.APPROVED:
                await session.commit()
                return PaymentOutcome(existing_payment, tickets_created)
            await session.commit()
            raise AppError(
                "PAYMENT_DECLINED",
                existing_payment.failure_reason or "Pagamento recusado.",
                402,
            )

        if reservation.status != ReservationStatus.PENDING:
            raise AppError(
                "RESERVATION_NOT_PAYABLE",
                "Esta reserva não pode ser paga.",
                409,
            )

        result = await gateway.authorize(
            amount=reservation.total_amount,
            card_number=data.card_number,
        )
        payment = Payment(
            reservation_id=reservation.id,
            amount=reservation.total_amount,
            status=result.status,
            provider=gateway.provider,
            failure_reason=result.failure_reason,
        )
        await add_payment(session, payment)

        if result.status == PaymentStatus.DECLINED:
            await session.commit()
            raise AppError(
                "PAYMENT_DECLINED",
                result.failure_reason or "Pagamento recusado.",
                402,
            )

        tickets = _build_tickets(
            reservation_id=reservation.id,
            event_id=reservation.event_id,
            owner_id=customer.id,
            quantity=reservation.quantity,
        )
        reservation.status = ReservationStatus.PAID
        await add_tickets(session, tickets)
        await session.commit()
        await session.refresh(payment)
        return PaymentOutcome(payment, len(tickets))
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "PAYMENT_FAILED",
            "Não foi possível concluir o pagamento.",
            409,
        ) from exc
