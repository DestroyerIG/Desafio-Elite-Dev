from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.tickets.repository import get_customer_ticket_for_update


class RecordingSession:
    query = None

    async def scalar(self, query):
        self.query = query
        return None


@pytest.mark.asyncio
async def test_ticket_share_query_uses_row_lock() -> None:
    session = RecordingSession()

    await get_customer_ticket_for_update(  # type: ignore[arg-type]
        session,
        uuid4(),
        uuid4(),
    )

    statement = str(
        session.query.compile(dialect=postgresql.dialect())  # type: ignore[union-attr]
    )
    assert "FOR UPDATE" in statement
