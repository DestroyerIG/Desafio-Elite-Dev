from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.reservations.repository import get_published_event_for_update


class RecordingSession:
    query = None

    async def scalar(self, query):
        self.query = query
        return None


@pytest.mark.asyncio
async def test_reservation_event_query_uses_row_lock() -> None:
    session = RecordingSession()

    await get_published_event_for_update(session, uuid4())  # type: ignore[arg-type]

    statement = str(
        session.query.compile(dialect=postgresql.dialect())  # type: ignore[union-attr]
    )
    assert "FOR UPDATE" in statement
