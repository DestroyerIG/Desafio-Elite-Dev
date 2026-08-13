from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.health.repository import check_database
from app.modules.health.schemas import HealthResponse


async def get_health_status(session: AsyncSession) -> HealthResponse:
    await check_database(session)
    return HealthResponse(status="ok")

