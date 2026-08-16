from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.gate.schemas import GateValidationCreate, GateValidationResponse
from app.modules.gate.service import validate_ticket


router = APIRouter(prefix="/api/v1/gate", tags=["gate"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
GateUser = Annotated[User, Depends(require_roles(UserRole.GATE))]


@router.post("/validate", response_model=GateValidationResponse)
async def validate_gate_ticket(
    data: GateValidationCreate,
    session: DatabaseSession,
    gate_user: GateUser,
) -> GateValidationResponse:
    outcome = await validate_ticket(session, gate_user, data)
    return GateValidationResponse(
        result=outcome.result,
        message=outcome.message,
        ticket_id=outcome.ticket_id,
        public_code=outcome.public_code,
        validated_at=outcome.validated_at,
    )
