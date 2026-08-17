from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.modules.seats.realtime import SeatMapHub
from app.modules.seats.repository import get_seats_for_update
from app.modules.seats.schemas import SeatHoldCreate, SeatMapConfigure


class RecordingSession:
    query = None

    async def scalars(self, query):
        self.query = query

        class EmptyResult:
            def __iter__(self):
                return iter(())

        return EmptyResult()


def test_seat_map_input_rejects_duplicate_section_names() -> None:
    with pytest.raises(ValidationError):
        SeatMapConfigure(
            stage_label="Palco",
            sections=[
                {"name": "Pista", "row_count": 1, "seats_per_row": 2},
                {"name": " pista ", "row_count": 1, "seats_per_row": 2},
            ],
        )


def test_seat_hold_rejects_duplicate_ids() -> None:
    seat_id = uuid4()
    with pytest.raises(ValidationError):
        SeatHoldCreate(seat_ids=[seat_id, seat_id])


@pytest.mark.asyncio
async def test_seat_selection_query_uses_row_lock() -> None:
    session = RecordingSession()

    await get_seats_for_update(  # type: ignore[arg-type]
        session,
        uuid4(),
        [uuid4(), uuid4()],
    )

    statement = str(
        session.query.compile(dialect=postgresql.dialect())  # type: ignore[union-attr]
    )
    assert "FOR UPDATE" in statement
    assert "ORDER BY" in statement


@pytest.mark.asyncio
async def test_realtime_hub_keeps_latest_version_for_slow_clients() -> None:
    hub = SeatMapHub()
    event_id = uuid4()

    async with hub.subscribe(event_id) as queue:
        await hub.publish(event_id, 2)
        await hub.publish(event_id, 3)

        assert await queue.get() == 3
