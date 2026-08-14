import os
from uuid import uuid4

import httpx
import pytest

from app.integrations.ticketmaster.client import get_ticketmaster_client
from app.main import app
from app.modules.catalog.schemas import CatalogEvent


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Defina RUN_INTEGRATION_TESTS=1 com um PostgreSQL isolado.",
    ),
]


class FakeCatalogClient:
    async def search_events(self, _query: str) -> list[CatalogEvent]:
        return [self.event()]

    async def get_event(self, external_id: str) -> CatalogEvent:
        event = self.event()
        return event.model_copy(update={"external_id": external_id})

    @staticmethod
    def event() -> CatalogEvent:
        return CatalogEvent(
            external_id="external-integration-test",
            title="Evento de Integração",
            description="Evento usado somente no banco isolado de teste.",
            image_url="https://s1.ticketm.net/dam/a/test.jpg",
            venue_name="Arena de Teste",
            venue_address="Rua de Teste, 10, São Paulo, SP, BR",
            event_date="2027-05-20T22:00:00Z",
        )


async def fake_catalog_dependency():
    yield FakeCatalogClient()


@pytest.mark.asyncio
async def test_auth_catalog_and_event_flow() -> None:
    app.dependency_overrides[get_ticketmaster_client] = fake_catalog_dependency
    unique_email = f"customer-{uuid4()}@example.com"
    external_id = f"external-{uuid4().hex}"

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "name": "Cliente Integração",
                    "email": unique_email,
                    "password": "Integration123!",
                },
            )
            assert register_response.status_code == 201
            assert register_response.json()["role"] == "CUSTOMER"

            customer_login = await client.post(
                "/api/v1/auth/login",
                json={"email": unique_email, "password": "Integration123!"},
            )
            organizer_login = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "organizer@example.com",
                    "password": "DevOnly123!",
                },
            )
            assert customer_login.status_code == 200
            assert organizer_login.status_code == 200
            customer_token = customer_login.json()["access_token"]
            organizer_token = organizer_login.json()["access_token"]

            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {customer_token}"},
            )
            assert me_response.status_code == 200
            assert me_response.json()["email"] == unique_email

            forbidden_response = await client.post(
                "/api/v1/events",
                headers={"Authorization": f"Bearer {customer_token}"},
                json={
                    "external_id": external_id,
                    "capacity": 50,
                    "ticket_price": "35.00",
                },
            )
            assert forbidden_response.status_code == 403

            catalog_response = await client.get(
                "/api/v1/catalog/events?q=evento",
                headers={"Authorization": f"Bearer {organizer_token}"},
            )
            assert catalog_response.status_code == 200
            assert len(catalog_response.json()) == 1

            create_response = await client.post(
                "/api/v1/events",
                headers={"Authorization": f"Bearer {organizer_token}"},
                json={
                    "external_id": external_id,
                    "capacity": 50,
                    "ticket_price": "35.00",
                },
            )
            assert create_response.status_code == 201
            created_event = create_response.json()
            assert created_event["status"] == "PUBLISHED"
            assert created_event["available_tickets"] == 50

            public_response = await client.get(
                f"/api/v1/events/{created_event['id']}"
            )
            assert public_response.status_code == 200
            assert public_response.json()["external_id"] == external_id

            update_response = await client.patch(
                f"/api/v1/events/{created_event['id']}",
                headers={"Authorization": f"Bearer {organizer_token}"},
                json={"title": "Evento Atualizado", "capacity": 75},
            )
            assert update_response.status_code == 200
            assert update_response.json()["title"] == "Evento Atualizado"
            assert update_response.json()["available_tickets"] == 75

            delete_response = await client.delete(
                f"/api/v1/events/{created_event['id']}",
                headers={"Authorization": f"Bearer {organizer_token}"},
            )
            assert delete_response.status_code == 204
    finally:
        app.dependency_overrides.clear()
