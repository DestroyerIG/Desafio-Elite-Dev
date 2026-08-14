from app.integrations.ticketmaster.client import TicketmasterClient


def test_ticketmaster_event_is_mapped_to_internal_contract() -> None:
    payload = {
        "id": "external-123",
        "name": "Festival de Teste",
        "info": "Descrição externa",
        "dates": {"start": {"dateTime": "2027-03-20T22:00:00Z"}},
        "images": [
            {
                "url": "https://s1.ticketm.net/dam/a/test.jpg",
                "ratio": "16_9",
                "width": 1024,
            }
        ],
        "_embedded": {
            "venues": [
                {
                    "name": "Arena Central",
                    "address": {"line1": "Rua Principal, 10"},
                    "city": {"name": "São Paulo"},
                    "state": {"stateCode": "SP"},
                    "country": {"countryCode": "BR"},
                }
            ]
        },
    }

    event = TicketmasterClient._map_event(payload)

    assert event.external_id == "external-123"
    assert event.title == "Festival de Teste"
    assert event.venue_name == "Arena Central"
    assert event.venue_address == "Rua Principal, 10, São Paulo, SP, BR"
    assert event.event_date.tzinfo is not None
