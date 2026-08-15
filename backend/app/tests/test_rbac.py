from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest

from app.database.session import get_db_session
from app.integrations.ticketmaster.client import get_ticketmaster_client
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import get_current_user


async def override_session() -> AsyncIterator[object]:
    yield object()


async def override_catalog() -> AsyncIterator[object]:
    yield object()


@pytest.mark.asyncio
async def test_customer_cannot_create_event() -> None:
    customer = User(
        id=uuid4(),
        name="Cliente",
        email="customer@test.local",
        password_hash="not-used",
        role=UserRole.CUSTOMER,
    )
    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_ticketmaster_client] = override_catalog

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/events",
                json={
                    "external_id": "external-123",
                    "capacity": 100,
                    "ticket_price": "50.00",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "FORBIDDEN",
            "message": "Você não tem permissão para esta ação.",
        }
    }


@pytest.mark.asyncio
async def test_organizer_cannot_create_reservation() -> None:
    organizer = User(
        id=uuid4(),
        name="Organizador",
        email="organizer@test.local",
        password_hash="not-used",
        role=UserRole.ORGANIZER,
    )
    app.dependency_overrides[get_current_user] = lambda: organizer
    app.dependency_overrides[get_db_session] = override_session

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/events/{uuid4()}/reservations",
                json={"quantity": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
