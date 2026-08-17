import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest

from app.database.session import async_session_factory, engine
from app.integrations.ticketmaster.client import get_ticketmaster_client
from app.main import app
from app.models.reservation import Reservation
from app.modules.catalog.schemas import CatalogEvent
from app.modules.seats.realtime import seat_map_hub, seat_map_runtime
from app.modules.seats.service import notify_seat_map_changed


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Defina RUN_INTEGRATION_TESTS=1 com um PostgreSQL isolado.",
    ),
]


class FakeSeatCatalogClient:
    async def get_event(self, external_id: str) -> CatalogEvent:
        return CatalogEvent(
            external_id=external_id,
            title="Arena com assentos",
            description="Evento para validar reservas de lugares marcados.",
            image_url=None,
            venue_name="Arena de teste",
            venue_address="Rua dos Testes, 10, São Paulo, SP, BR",
            event_date=datetime.now(UTC) + timedelta(days=30),
        )


async def fake_seat_catalog_dependency():
    yield FakeSeatCatalogClient()


async def login(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "DevOnly123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_postgres_notification_reaches_realtime_hub() -> None:
    event_id = uuid4()
    await seat_map_runtime.start()
    try:
        async with seat_map_hub.subscribe(event_id) as queue:
            received_version: int | None = None
            for _ in range(10):
                async with async_session_factory() as session:
                    await notify_seat_map_changed(session, event_id, 7)
                    await session.commit()
                try:
                    received_version = await asyncio.wait_for(
                        queue.get(), timeout=0.5
                    )
                    break
                except TimeoutError:
                    continue
            assert received_version == 7
    finally:
        await seat_map_runtime.stop()
        await engine.dispose()


@pytest.mark.asyncio
async def test_assigned_seat_lifecycle_is_atomic_and_returns_stock() -> None:
    app.dependency_overrides[get_ticketmaster_client] = (
        fake_seat_catalog_dependency
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            organizer_headers, first_headers, second_headers = await asyncio.gather(
                login(client, "organizer@example.com"),
                login(client, "customer1@example.com"),
                login(client, "customer2@example.com"),
            )
            event_response = await client.post(
                "/api/v1/events",
                headers=organizer_headers,
                json={
                    "external_id": f"seat-map-{uuid4().hex}",
                    "capacity": 2,
                    "ticket_price": "75.00",
                },
            )
            assert event_response.status_code == 201
            event_id = event_response.json()["id"]
            assert event_response.json()["seating_mode"] == "GENERAL_ADMISSION"

            map_response = await client.put(
                f"/api/v1/organizer/events/{event_id}/seat-map",
                headers=organizer_headers,
                json={
                    "stage_label": "Palco principal",
                    "sections": [
                        {"name": "Pista", "row_count": 1, "seats_per_row": 2}
                    ],
                },
            )
            assert map_response.status_code == 200
            seats = map_response.json()["sections"][0]["seats"]
            assert [seat["label"] for seat in seats] == ["A1", "A2"]

            bypass_response = await client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=first_headers,
                json={"quantity": 1},
            )
            assert bypass_response.status_code == 409
            assert bypass_response.json()["error"]["code"] == "SEAT_SELECTION_REQUIRED"

            first_seat_id = seats[0]["id"]
            concurrent_holds = await asyncio.gather(
                client.post(
                    f"/api/v1/events/{event_id}/seat-holds",
                    headers=first_headers,
                    json={"seat_ids": [first_seat_id]},
                ),
                client.post(
                    f"/api/v1/events/{event_id}/seat-holds",
                    headers=second_headers,
                    json={"seat_ids": [first_seat_id]},
                ),
            )
            assert sorted(response.status_code for response in concurrent_holds) == [
                201,
                409,
            ]
            winning_index = next(
                index
                for index, response in enumerate(concurrent_holds)
                if response.status_code == 201
            )
            winner_headers = (first_headers, second_headers)[winning_index]
            loser_headers = (first_headers, second_headers)[1 - winning_index]
            winning_reservation = concurrent_holds[winning_index].json()
            assert winning_reservation["expires_at"] is not None
            assert winning_reservation["seats"][0]["id"] == first_seat_id

            payment = await client.post(
                f"/api/v1/reservations/{winning_reservation['id']}/payments",
                headers=winner_headers,
                json={"card_number": "4242424242424242"},
            )
            assert payment.status_code == 201
            ticket = await client.get(
                f"/api/v1/tickets/{payment.json()['ticket_ids'][0]}",
                headers=winner_headers,
            )
            assert ticket.status_code == 200
            assert ticket.json()["seat"]["id"] == first_seat_id

            expiring_hold = await client.post(
                f"/api/v1/events/{event_id}/seat-holds",
                headers=loser_headers,
                json={"seat_ids": [seats[1]["id"]]},
            )
            assert expiring_hold.status_code == 201
            async with async_session_factory() as session:
                reservation = await session.get(
                    Reservation, UUID(expiring_hold.json()["id"])
                )
                assert reservation is not None
                reservation.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await session.commit()

            expired_payment = await client.post(
                f"/api/v1/reservations/{expiring_hold.json()['id']}/payments",
                headers=loser_headers,
                json={"card_number": "4242424242424242"},
            )
            assert expired_payment.status_code == 409
            assert expired_payment.json()["error"]["code"] == "RESERVATION_EXPIRED"

            map_after_expiry = await client.get(
                f"/api/v1/events/{event_id}/seat-map"
            )
            assert map_after_expiry.status_code == 200
            assert [
                seat["status"]
                for seat in map_after_expiry.json()["sections"][0]["seats"]
            ] == ["SOLD", "AVAILABLE"]

            refund = await client.post(
                f"/api/v1/reservations/{winning_reservation['id']}/refunds",
                headers=winner_headers,
            )
            assert refund.status_code == 201
            assert refund.json()["reservation"]["status"] == "REFUNDED"
            assert refund.json()["reservation"]["seats"][0]["id"] == first_seat_id

            final_map, final_event = await asyncio.gather(
                client.get(f"/api/v1/events/{event_id}/seat-map"),
                client.get(f"/api/v1/events/{event_id}"),
            )
            assert all(
                seat["status"] == "AVAILABLE"
                for seat in final_map.json()["sections"][0]["seats"]
            )
            assert final_event.json()["available_tickets"] == 2

            locked_map = await client.put(
                f"/api/v1/organizer/events/{event_id}/seat-map",
                headers=organizer_headers,
                json={
                    "stage_label": "Outro palco",
                    "sections": [
                        {"name": "Outro setor", "row_count": 1, "seats_per_row": 2}
                    ],
                },
            )
            assert locked_map.status_code == 409
            assert locked_map.json()["error"]["code"] == "SEAT_MAP_LOCKED"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
