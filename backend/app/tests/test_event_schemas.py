from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.events.schemas import CustomEventCreate


def custom_event_payload() -> dict[str, object]:
    return {
        "title": "  Evento independente  ",
        "description": "  Uma programação criada pelo organizador.  ",
        "venue_name": "  Espaço Cultural  ",
        "venue_address": "  Rua da Plataforma, 100  ",
        "event_date": datetime.now(UTC) + timedelta(days=30),
        "capacity": 200,
        "ticket_price": "35.90",
    }


def test_custom_event_normalizes_text_fields() -> None:
    event = CustomEventCreate.model_validate(custom_event_payload())

    assert event.title == "Evento independente"
    assert event.description == "Uma programação criada pelo organizador."
    assert event.venue_name == "Espaço Cultural"
    assert event.venue_address == "Rua da Plataforma, 100"


@pytest.mark.parametrize(
    "event_date",
    [
        datetime.now(UTC) - timedelta(minutes=1),
        datetime.now().replace(microsecond=0),
    ],
)
def test_custom_event_rejects_past_or_timezone_naive_date(event_date: datetime) -> None:
    payload = custom_event_payload()
    payload["event_date"] = event_date

    with pytest.raises(ValidationError):
        CustomEventCreate.model_validate(payload)
