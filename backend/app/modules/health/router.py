from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.health.schemas import HealthResponse
from app.modules.health.service import get_health_status


router = APIRouter(tags=["health"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/health", response_model=HealthResponse)
async def health(session: DatabaseSession) -> HealthResponse:
    return await get_health_status(session)

