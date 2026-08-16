from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_hex
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_ticket_token, hash_ticket_token
from app.models.enums import (
    EventStatus,
    PaymentStatus,
    RefundStatus,
    ReservationStatus,
    TicketStatus,
)
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.reservation import Reservation
from app.models.ticket import Ticket
from app.models.user import User
from app.modules.payments.gateway import PaymentGateway
from app.modules.payments.repository import (
    add_payment,
    add_refund,
    add_tickets,
    get_approved_payment,
    get_refund_for_reservation,
    list_tickets_for_reservation_for_update,
    list_ticket_ids_for_reservation,
    revoke_ticket_shares,
)
from app.modules.payments.schemas import PaymentCreate
from app.modules.reservations.repository import (
    get_customer_reservation,
    get_event_for_update,
)


REFUND_REQUEST_WINDOW = timedelta(days=7)
REFUND_EVENT_DEADLINE = timedelta(hours=48)


@dataclass(frozen=True, slots=True)
class PaymentOutcome:
    payment: Payment
    ticket_ids: list[UUID]

    @property
    def tickets_created(self) -> int:
        return len(self.ticket_ids)


@dataclass(frozen=True, slots=True)
class RefundOutcome:
    refund: Refund
    reservation: Reservation
    tickets_refunded: int


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

        if reservation.status == ReservationStatus.PAID:
            approved_payment = await get_approved_payment(session, reservation.id)
            if approved_payment is None:
                raise AppError(
                    "PAYMENT_STATE_INVALID",
                    "A reserva paga não possui um pagamento aprovado.",
                    409,
                )
            ticket_ids = await list_ticket_ids_for_reservation(
                session, reservation.id
            )
            if not ticket_ids:
                raise AppError(
                    "PAYMENT_STATE_INVALID",
                    "A reserva paga não possui ingressos emitidos.",
                    409,
                )
            await session.commit()
            return PaymentOutcome(approved_payment, ticket_ids)

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
        return PaymentOutcome(payment, sorted(ticket.id for ticket in tickets))
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


async def refund_paid_reservation(
    session: AsyncSession,
    customer: User,
    reservation_id: UUID,
    gateway: PaymentGateway,
) -> RefundOutcome:
    try:
        existing_reservation = await get_customer_reservation(
            session, reservation_id, customer.id
        )
        if existing_reservation is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reserva não encontrada.", 404)

        event = await get_event_for_update(session, existing_reservation.event_id)
        reservation = await get_customer_reservation(
            session,
            reservation_id,
            customer.id,
            for_update=True,
        )
        if event is None or reservation is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reserva não encontrada.", 404)

        existing_refund = await get_refund_for_reservation(session, reservation.id)
        if reservation.status == ReservationStatus.REFUNDED:
            if (
                existing_refund is None
                or existing_refund.status != RefundStatus.APPROVED
            ):
                raise AppError(
                    "REFUND_STATE_INVALID",
                    "A reserva reembolsada não possui um reembolso aprovado.",
                    409,
                )
            await session.commit()
            await session.refresh(reservation)
            return RefundOutcome(
                existing_refund,
                reservation,
                reservation.quantity,
            )

        if reservation.status != ReservationStatus.PAID:
            raise AppError(
                "RESERVATION_NOT_REFUNDABLE",
                "Somente reservas pagas podem ser reembolsadas.",
                409,
            )

        payment = await get_approved_payment(session, reservation.id)
        if payment is None:
            raise AppError(
                "REFUND_STATE_INVALID",
                "A reserva não possui um pagamento aprovado para reembolso.",
                409,
            )

        now = datetime.now(UTC)
        if event.status != EventStatus.CANCELLED:
            if payment.created_at < now - REFUND_REQUEST_WINDOW:
                raise AppError(
                    "REFUND_WINDOW_EXPIRED",
                    "O prazo de 7 dias para solicitar o reembolso terminou.",
                    409,
                )
            if event.event_date < now + REFUND_EVENT_DEADLINE:
                raise AppError(
                    "REFUND_EVENT_TOO_CLOSE",
                    "O reembolso deve ser solicitado com pelo menos 48 horas de antecedência.",
                    409,
                )

        tickets = await list_tickets_for_reservation_for_update(
            session, reservation.id
        )
        if len(tickets) != reservation.quantity:
            raise AppError(
                "REFUND_STATE_INVALID",
                "A quantidade de ingressos emitidos não corresponde à reserva.",
                409,
            )
        if any(ticket.status == TicketStatus.USED for ticket in tickets):
            raise AppError(
                "REFUND_TICKET_USED",
                "Reservas com ingresso já utilizado não podem ser reembolsadas.",
                409,
            )
        if any(ticket.status != TicketStatus.ACTIVE for ticket in tickets):
            raise AppError(
                "REFUND_STATE_INVALID",
                "Todos os ingressos devem estar ativos para o reembolso integral.",
                409,
            )

        if (
            existing_refund is not None
            and existing_refund.status == RefundStatus.PENDING
        ):
            await session.commit()
            await session.refresh(reservation)
            return RefundOutcome(existing_refund, reservation, 0)

        result = await gateway.refund(
            payment_id=payment.id,
            amount=payment.amount,
        )
        refund = existing_refund or Refund(
            reservation_id=reservation.id,
            payment_id=payment.id,
            amount=payment.amount,
            status=RefundStatus.PENDING,
            provider=gateway.provider,
        )
        refund.status = result.status
        refund.failure_reason = result.failure_reason
        refund.processed_at = now if result.status != RefundStatus.PENDING else None
        if existing_refund is None:
            await add_refund(session, refund)

        if result.status == RefundStatus.FAILED:
            await session.commit()
            raise AppError(
                "REFUND_FAILED",
                result.failure_reason or "O reembolso foi recusado pelo simulador.",
                409,
            )
        if result.status == RefundStatus.PENDING:
            await session.commit()
            await session.refresh(reservation)
            return RefundOutcome(refund, reservation, 0)

        ticket_ids = [ticket.id for ticket in tickets]
        event.available_tickets += reservation.quantity
        reservation.status = ReservationStatus.REFUNDED
        for ticket in tickets:
            ticket.status = TicketStatus.REFUNDED
        await revoke_ticket_shares(session, ticket_ids, now)

        await session.commit()
        await session.refresh(refund)
        await session.refresh(reservation)
        return RefundOutcome(refund, reservation, len(tickets))
    except AppError:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "REFUND_FAILED",
            "Não foi possível concluir o reembolso.",
            409,
        ) from exc
