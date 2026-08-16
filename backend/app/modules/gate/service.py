from dataclasses import dataclass
from datetime import UTC, datetime
from hmac import compare_digest
from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import decode_ticket_token, hash_ticket_token
from app.models.enums import TicketStatus, ValidationResult
from app.models.ticket import Ticket, TicketValidation
from app.models.user import User
from app.modules.gate.repository import (
    add_ticket_validation,
    get_event,
    get_ticket_by_id_for_update,
    get_ticket_by_public_code_for_update,
)
from app.modules.gate.schemas import GateValidationCreate


@dataclass(frozen=True, slots=True)
class GateValidationOutcome:
    result: ValidationResult
    message: str
    ticket_id: UUID | None
    public_code: str | None
    validated_at: datetime


RESULT_MESSAGES = {
    ValidationResult.VALID: "Ingresso válido. Entrada liberada.",
    ValidationResult.INVALID: "Ingresso inválido.",
    ValidationResult.ALREADY_USED: "Este ingresso já foi utilizado.",
    ValidationResult.WRONG_EVENT: "Este ingresso pertence a outro evento.",
}


async def validate_ticket(
    session: AsyncSession,
    gate_user: User,
    data: GateValidationCreate,
) -> GateValidationOutcome:
    try:
        event = await get_event(session, data.event_id)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "Evento não encontrado.", 404)

        ticket = await _resolve_ticket_for_update(session, data.credential)
        result = _validation_result(ticket, data.event_id, data.credential)

        if result == ValidationResult.VALID and ticket is not None:
            ticket.status = TicketStatus.USED
            ticket.used_at = datetime.now(UTC)

        validation = TicketValidation(
            ticket_id=ticket.id if ticket is not None else None,
            gate_user_id=gate_user.id,
            event_id=data.event_id,
            result=result,
        )
        await add_ticket_validation(session, validation)
        await session.commit()
        return GateValidationOutcome(
            result=result,
            message=RESULT_MESSAGES[result],
            ticket_id=ticket.id if ticket is not None else None,
            public_code=ticket.public_code if ticket is not None else None,
            validated_at=validation.validated_at,
        )
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise


async def _resolve_ticket_for_update(
    session: AsyncSession,
    credential: str,
) -> Ticket | None:
    public_code = credential.upper()
    if public_code.startswith("ELT-"):
        return await get_ticket_by_public_code_for_update(session, public_code)

    try:
        payload = decode_ticket_token(credential)
        ticket_id = UUID(payload["ticket_id"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    return await get_ticket_by_id_for_update(session, ticket_id)


def _validation_result(
    ticket: Ticket | None,
    event_id: UUID,
    credential: str,
) -> ValidationResult:
    if ticket is None:
        return ValidationResult.INVALID

    if not credential.upper().startswith("ELT-"):
        try:
            payload = decode_ticket_token(credential)
            token_event_id = UUID(payload["event_id"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            return ValidationResult.INVALID
        if token_event_id != ticket.event_id or not compare_digest(
            hash_ticket_token(credential),
            ticket.qr_token_hash,
        ):
            return ValidationResult.INVALID

    if ticket.event_id != event_id:
        return ValidationResult.WRONG_EVENT
    if ticket.status == TicketStatus.USED:
        return ValidationResult.ALREADY_USED
    if ticket.status != TicketStatus.ACTIVE:
        return ValidationResult.INVALID
    return ValidationResult.VALID
