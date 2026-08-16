import asyncio
import os
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core.security import create_ticket_token, hash_opaque_token
from app.database.session import async_session_factory, engine
from app.integrations.ticketmaster.client import get_ticketmaster_client
from app.main import app
from app.models.enums import TicketStatus, ValidationResult
from app.models.payment import Payment
from app.models.ticket import Ticket, TicketShare, TicketValidation
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
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_reservations_do_not_oversell() -> None:
    app.dependency_overrides[get_ticketmaster_client] = fake_catalog_dependency
    external_id = f"reservation-{uuid4().hex}"

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            organizer_login, customer_one_login, customer_two_login = await asyncio.gather(
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "organizer@example.com",
                        "password": "DevOnly123!",
                    },
                ),
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "customer1@example.com",
                        "password": "DevOnly123!",
                    },
                ),
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "customer2@example.com",
                        "password": "DevOnly123!",
                    },
                ),
            )
            assert organizer_login.status_code == 200
            assert customer_one_login.status_code == 200
            assert customer_two_login.status_code == 200

            organizer_headers = {
                "Authorization": f"Bearer {organizer_login.json()['access_token']}"
            }
            customer_headers = [
                {
                    "Authorization": (
                        f"Bearer {customer_one_login.json()['access_token']}"
                    )
                },
                {
                    "Authorization": (
                        f"Bearer {customer_two_login.json()['access_token']}"
                    )
                },
            ]
            event_response = await client.post(
                "/api/v1/events",
                headers=organizer_headers,
                json={
                    "external_id": external_id,
                    "capacity": 1,
                    "ticket_price": "25.00",
                },
            )
            assert event_response.status_code == 201
            event_id = event_response.json()["id"]

            reservation_responses = await asyncio.gather(
                *(
                    client.post(
                        f"/api/v1/events/{event_id}/reservations",
                        headers=headers,
                        json={"quantity": 1},
                    )
                    for headers in customer_headers
                )
            )
            assert sorted(response.status_code for response in reservation_responses) == [
                201,
                409,
            ]

            winner_index = next(
                index
                for index, response in enumerate(reservation_responses)
                if response.status_code == 201
            )
            loser_index = 1 - winner_index
            reservation = reservation_responses[winner_index].json()
            assert reservation["quantity"] == 1
            assert reservation["unit_price"] == "25.00"
            assert reservation["total_amount"] == "25.00"
            assert reservation["status"] == "PENDING"
            assert reservation["expires_at"] is None
            assert (
                reservation_responses[loser_index].json()["error"]["code"]
                == "EVENT_SOLD_OUT"
            )

            event_after_reservation = await client.get(
                f"/api/v1/events/{event_id}"
            )
            assert event_after_reservation.json()["available_tickets"] == 0

            own_reservation = await client.get(
                f"/api/v1/reservations/{reservation['id']}",
                headers=customer_headers[winner_index],
            )
            hidden_from_other_customer = await client.get(
                f"/api/v1/reservations/{reservation['id']}",
                headers=customer_headers[loser_index],
            )
            assert own_reservation.status_code == 200
            assert hidden_from_other_customer.status_code == 404

            cancel_responses = await asyncio.gather(
                client.post(
                    f"/api/v1/reservations/{reservation['id']}/cancel",
                    headers=customer_headers[winner_index],
                ),
                client.post(
                    f"/api/v1/reservations/{reservation['id']}/cancel",
                    headers=customer_headers[winner_index],
                ),
            )
            assert all(response.status_code == 200 for response in cancel_responses)
            assert all(
                response.json()["status"] == "CANCELLED"
                for response in cancel_responses
            )

            event_after_cancellation = await client.get(
                f"/api/v1/events/{event_id}"
            )
            assert event_after_cancellation.json()["available_tickets"] == 1

            excessive_quantity = await client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=customer_headers[loser_index],
                json={"quantity": 2},
            )
            assert excessive_quantity.status_code == 409
            assert (
                excessive_quantity.json()["error"]["code"]
                == "INSUFFICIENT_TICKETS"
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_payment_issues_exact_ticket_quantity_and_protects_qr() -> None:
    app.dependency_overrides[get_ticketmaster_client] = fake_catalog_dependency
    external_id = f"payment-{uuid4().hex}"

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            organizer_login, customer_login, other_customer_login = await asyncio.gather(
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "organizer@example.com",
                        "password": "DevOnly123!",
                    },
                ),
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "customer1@example.com",
                        "password": "DevOnly123!",
                    },
                ),
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "customer2@example.com",
                        "password": "DevOnly123!",
                    },
                ),
            )
            assert organizer_login.status_code == 200
            assert customer_login.status_code == 200
            assert other_customer_login.status_code == 200

            organizer_headers = {
                "Authorization": f"Bearer {organizer_login.json()['access_token']}"
            }
            customer_headers = {
                "Authorization": f"Bearer {customer_login.json()['access_token']}"
            }
            other_customer_headers = {
                "Authorization": (
                    f"Bearer {other_customer_login.json()['access_token']}"
                )
            }
            event_response = await client.post(
                "/api/v1/events",
                headers=organizer_headers,
                json={
                    "external_id": external_id,
                    "capacity": 5,
                    "ticket_price": "30.00",
                },
            )
            assert event_response.status_code == 201
            event_id = event_response.json()["id"]

            declined_reservation = await client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=customer_headers,
                json={"quantity": 1},
            )
            assert declined_reservation.status_code == 201
            declined_reservation_id = declined_reservation.json()["id"]

            declined_payment = await client.post(
                f"/api/v1/reservations/{declined_reservation_id}/payments",
                headers=customer_headers,
                json={"card_number": "4000000000000000"},
            )
            assert declined_payment.status_code == 402
            assert declined_payment.json()["error"]["code"] == "PAYMENT_DECLINED"

            tickets_after_decline = await client.get(
                "/api/v1/me/tickets",
                headers=customer_headers,
            )
            assert not any(
                ticket["reservation_id"] == declined_reservation_id
                for ticket in tickets_after_decline.json()
            )

            own_reservations = await client.get(
                "/api/v1/me/reservations",
                headers=customer_headers,
            )
            other_customer_reservations = await client.get(
                "/api/v1/me/reservations",
                headers=other_customer_headers,
            )
            assert own_reservations.status_code == 200
            assert any(
                reservation["id"] == declined_reservation_id
                and reservation["status"] == "PENDING"
                and reservation["event"]["id"] == event_id
                for reservation in own_reservations.json()
            )
            assert not any(
                reservation["id"] == declined_reservation_id
                for reservation in other_customer_reservations.json()
            )

            declined_retry = await client.post(
                f"/api/v1/reservations/{declined_reservation_id}/payments",
                headers=customer_headers,
                json={"card_number": "4242424242424242"},
            )
            assert declined_retry.status_code == 201
            assert declined_retry.json()["status"] == "APPROVED"
            assert declined_retry.json()["tickets_created"] == 1
            assert len(declined_retry.json()["ticket_ids"]) == 1
            declined_detail = await client.get(
                f"/api/v1/reservations/{declined_reservation_id}",
                headers=customer_headers,
            )
            assert declined_detail.json()["status"] == "PAID"

            async with async_session_factory() as session:
                attempt_count = await session.scalar(
                    select(func.count(Payment.id)).where(
                        Payment.reservation_id == declined_reservation_id
                    )
                )
            assert attempt_count == 2

            approved_reservation = await client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=customer_headers,
                json={"quantity": 3},
            )
            assert approved_reservation.status_code == 201
            approved_reservation_id = approved_reservation.json()["id"]

            approved_payment = await client.post(
                f"/api/v1/reservations/{approved_reservation_id}/payments",
                headers=customer_headers,
                json={"card_number": "4242 4242 4242 4242"},
            )
            assert approved_payment.status_code == 201
            assert approved_payment.json()["status"] == "APPROVED"
            assert approved_payment.json()["tickets_created"] == 3
            assert len(approved_payment.json()["ticket_ids"]) == 3

            approved_detail = await client.get(
                f"/api/v1/reservations/{approved_reservation_id}",
                headers=customer_headers,
            )
            assert approved_detail.json()["status"] == "PAID"

            tickets_response = await client.get(
                "/api/v1/me/tickets",
                headers=customer_headers,
            )
            assert tickets_response.status_code == 200
            approved_tickets = [
                ticket
                for ticket in tickets_response.json()
                if ticket["reservation_id"] == approved_reservation_id
            ]
            retried_tickets = [
                ticket
                for ticket in tickets_response.json()
                if ticket["reservation_id"] == declined_reservation_id
            ]
            assert len(approved_tickets) == 3
            assert len(retried_tickets) == 1
            assert len({ticket["public_code"] for ticket in approved_tickets}) == 3

            ticket_id = approved_tickets[0]["id"]
            own_detail = await client.get(
                f"/api/v1/tickets/{ticket_id}",
                headers=customer_headers,
            )
            hidden_from_other_customer = await client.get(
                f"/api/v1/tickets/{ticket_id}",
                headers=other_customer_headers,
            )
            assert own_detail.status_code == 200
            assert own_detail.json()["event"]["id"] == event_id
            assert hidden_from_other_customer.status_code == 404

            qr_response = await client.get(
                f"/api/v1/tickets/{ticket_id}/qr",
                headers=customer_headers,
            )
            assert qr_response.status_code == 200
            assert qr_response.headers["content-type"] == "image/png"
            assert qr_response.headers["cache-control"] == "private, no-store"
            assert qr_response.content.startswith(b"\x89PNG\r\n\x1a\n")

            repeated_payment = await client.post(
                f"/api/v1/reservations/{approved_reservation_id}/payments",
                headers=customer_headers,
                json={"card_number": "5555555555554444"},
            )
            assert repeated_payment.status_code == 201
            assert repeated_payment.json()["id"] == approved_payment.json()["id"]
            assert repeated_payment.json()["tickets_created"] == 3
            assert repeated_payment.json()["ticket_ids"] == approved_payment.json()[
                "ticket_ids"
            ]

            concurrent_reservation = await client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=customer_headers,
                json={"quantity": 1},
            )
            assert concurrent_reservation.status_code == 201
            concurrent_reservation_id = concurrent_reservation.json()["id"]
            concurrent_payments = await asyncio.gather(
                client.post(
                    f"/api/v1/reservations/{concurrent_reservation_id}/payments",
                    headers=customer_headers,
                    json={"card_number": "4242424242424242"},
                ),
                client.post(
                    f"/api/v1/reservations/{concurrent_reservation_id}/payments",
                    headers=customer_headers,
                    json={"card_number": "5555555555554444"},
                ),
            )
            assert all(response.status_code == 201 for response in concurrent_payments)
            assert len({response.json()["id"] for response in concurrent_payments}) == 1
            assert all(
                len(response.json()["ticket_ids"]) == 1
                for response in concurrent_payments
            )
            assert len(
                {
                    response.json()["ticket_ids"][0]
                    for response in concurrent_payments
                }
            ) == 1

            tickets_after_retry = await client.get(
                "/api/v1/me/tickets",
                headers=customer_headers,
            )
            assert len(
                [
                    ticket
                    for ticket in tickets_after_retry.json()
                    if ticket["reservation_id"] == approved_reservation_id
                ]
            ) == 3
            assert len(
                [
                    ticket
                    for ticket in tickets_after_retry.json()
                    if ticket["reservation_id"] == concurrent_reservation_id
                ]
            ) == 1
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_sharing_and_gate_validation_are_secure_and_atomic() -> None:
    app.dependency_overrides[get_ticketmaster_client] = fake_catalog_dependency
    first_external_id = f"gate-first-{uuid4().hex}"
    second_external_id = f"gate-second-{uuid4().hex}"

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            organizer_login, customer_login, other_customer_login, gate_login = (
                await asyncio.gather(
                    client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "organizer@example.com",
                            "password": "DevOnly123!",
                        },
                    ),
                    client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "customer1@example.com",
                            "password": "DevOnly123!",
                        },
                    ),
                    client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "customer2@example.com",
                            "password": "DevOnly123!",
                        },
                    ),
                    client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "gate@example.com",
                            "password": "DevOnly123!",
                        },
                    ),
                )
            )
            assert all(
                response.status_code == 200
                for response in (
                    organizer_login,
                    customer_login,
                    other_customer_login,
                    gate_login,
                )
            )

            organizer_headers = {
                "Authorization": f"Bearer {organizer_login.json()['access_token']}"
            }
            customer_headers = {
                "Authorization": f"Bearer {customer_login.json()['access_token']}"
            }
            other_customer_headers = {
                "Authorization": (
                    f"Bearer {other_customer_login.json()['access_token']}"
                )
            }
            gate_headers = {
                "Authorization": f"Bearer {gate_login.json()['access_token']}"
            }

            first_event = await client.post(
                "/api/v1/events",
                headers=organizer_headers,
                json={
                    "external_id": first_external_id,
                    "capacity": 1,
                    "ticket_price": "40.00",
                },
            )
            second_event = await client.post(
                "/api/v1/events",
                headers=organizer_headers,
                json={
                    "external_id": second_external_id,
                    "capacity": 1,
                    "ticket_price": "50.00",
                },
            )
            assert first_event.status_code == 201
            assert second_event.status_code == 201
            first_event_id = first_event.json()["id"]
            second_event_id = second_event.json()["id"]

            reservation = await client.post(
                f"/api/v1/events/{first_event_id}/reservations",
                headers=customer_headers,
                json={"quantity": 1},
            )
            assert reservation.status_code == 201
            payment = await client.post(
                f"/api/v1/reservations/{reservation.json()['id']}/payments",
                headers=customer_headers,
                json={"card_number": "4242424242424242"},
            )
            assert payment.status_code == 201
            ticket_id = payment.json()["ticket_ids"][0]

            ticket_detail = await client.get(
                f"/api/v1/tickets/{ticket_id}",
                headers=customer_headers,
            )
            assert ticket_detail.status_code == 200
            public_code = ticket_detail.json()["public_code"]

            hidden_share = await client.post(
                f"/api/v1/tickets/{ticket_id}/share",
                headers=other_customer_headers,
            )
            assert hidden_share.status_code == 404

            share = await client.post(
                f"/api/v1/tickets/{ticket_id}/share",
                headers=customer_headers,
            )
            assert share.status_code == 201
            share_token = share.json()["token"]
            assert share.json()["expires_at"] is None

            shared_detail = await client.get(
                f"/api/v1/shared-tickets/{share_token}"
            )
            shared_qr = await client.get(
                f"/api/v1/shared-tickets/{share_token}/qr"
            )
            invalid_share = await client.get(
                "/api/v1/shared-tickets/token-inexistente"
            )
            assert shared_detail.status_code == 200
            assert set(shared_detail.json()) == {
                "public_code",
                "status",
                "used_at",
                "event",
            }
            assert shared_detail.json()["public_code"] == public_code
            assert shared_qr.status_code == 200
            assert shared_qr.content.startswith(b"\x89PNG\r\n\x1a\n")
            assert invalid_share.status_code == 404

            async with async_session_factory() as session:
                stored_share_hash = await session.scalar(
                    select(TicketShare.token_hash).where(
                        TicketShare.ticket_id == UUID(ticket_id)
                    )
                )
            assert stored_share_hash == hash_opaque_token(share_token)
            assert share_token != stored_share_hash

            forbidden_gate = await client.post(
                "/api/v1/gate/validate",
                headers=customer_headers,
                json={"event_id": first_event_id, "credential": public_code},
            )
            assert forbidden_gate.status_code == 403

            wrong_event = await client.post(
                "/api/v1/gate/validate",
                headers=gate_headers,
                json={"event_id": second_event_id, "credential": public_code},
            )
            invalid_code = await client.post(
                "/api/v1/gate/validate",
                headers=gate_headers,
                json={
                    "event_id": first_event_id,
                    "credential": "ELT-NAO-EXISTE",
                },
            )
            assert wrong_event.json()["result"] == "WRONG_EVENT"
            assert invalid_code.json()["result"] == "INVALID"

            qr_token = create_ticket_token(
                UUID(ticket_id),
                UUID(first_event_id),
            )
            token_parts = qr_token.split(".")
            signature = token_parts[2]
            middle = len(signature) // 2
            token_parts[2] = (
                signature[:middle]
                + ("a" if signature[middle] != "a" else "b")
                + signature[middle + 1 :]
            )
            tampered_qr = ".".join(token_parts)
            tampered_validation = await client.post(
                "/api/v1/gate/validate",
                headers=gate_headers,
                json={"event_id": first_event_id, "credential": tampered_qr},
            )
            assert tampered_validation.json()["result"] == "INVALID"

            concurrent_validations = await asyncio.gather(
                client.post(
                    "/api/v1/gate/validate",
                    headers=gate_headers,
                    json={"event_id": first_event_id, "credential": qr_token},
                ),
                client.post(
                    "/api/v1/gate/validate",
                    headers=gate_headers,
                    json={"event_id": first_event_id, "credential": public_code},
                ),
            )
            assert all(
                response.status_code == 200 for response in concurrent_validations
            )
            assert sorted(
                response.json()["result"] for response in concurrent_validations
            ) == ["ALREADY_USED", "VALID"]

            third_validation = await client.post(
                "/api/v1/gate/validate",
                headers=gate_headers,
                json={"event_id": first_event_id, "credential": public_code},
            )
            assert third_validation.json()["result"] == "ALREADY_USED"

            shared_after_use = await client.get(
                f"/api/v1/shared-tickets/{share_token}"
            )
            assert shared_after_use.json()["status"] == "USED"

            async with async_session_factory() as session:
                ticket = await session.get(Ticket, UUID(ticket_id))
                validation_results = list(
                    await session.scalars(
                        select(TicketValidation.result).where(
                            TicketValidation.ticket_id == UUID(ticket_id)
                        )
                    )
                )
                invalid_without_ticket = await session.scalar(
                    select(func.count(TicketValidation.id)).where(
                        TicketValidation.event_id == UUID(first_event_id),
                        TicketValidation.ticket_id.is_(None),
                        TicketValidation.result == ValidationResult.INVALID,
                    )
                )
            assert ticket is not None
            assert ticket.status == TicketStatus.USED
            assert ticket.used_at is not None
            assert validation_results.count(ValidationResult.VALID) == 1
            assert validation_results.count(ValidationResult.ALREADY_USED) == 2
            assert validation_results.count(ValidationResult.WRONG_EVENT) == 1
            assert invalid_without_ticket == 2
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
