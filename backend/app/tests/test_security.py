import logging
from uuid import uuid4

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_ticket_token,
    decode_access_token,
    decode_ticket_token,
    hash_ticket_token,
    hash_password,
    verify_password,
)
from app.core.logging import SensitivePathFilter
from app.models.enums import UserRole


def test_password_hash_is_verified_without_storing_plain_text() -> None:
    password = "StrongTest123!"

    password_hash = hash_password(password)

    assert password not in password_hash
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_contains_only_required_identity_claims() -> None:
    user_id = uuid4()

    token = create_access_token(user_id, UserRole.CUSTOMER)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == UserRole.CUSTOMER.value
    assert set(payload) == {"sub", "role", "iat", "exp"}


def test_production_rejects_documented_placeholder_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="replace-with-a-long-random-secret-at-least-32-chars",
            ticket_secret="configured-independent-ticket-secret-123",
        )


def test_production_rejects_documented_placeholder_ticket_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="configured-production-jwt-secret-123456",
            ticket_secret="replace-with-an-independent-long-random-secret",
        )


def test_ticket_token_has_only_the_required_signed_payload() -> None:
    ticket_id = uuid4()
    event_id = uuid4()

    token = create_ticket_token(ticket_id, event_id)
    payload = decode_ticket_token(token)

    assert payload == {
        "ticket_id": str(ticket_id),
        "event_id": str(event_id),
        "type": "ticket",
    }
    assert len(hash_ticket_token(token)) == 64


def test_tampered_ticket_token_is_rejected() -> None:
    tampered_token = jwt.encode(
        {
            "ticket_id": str(uuid4()),
            "event_id": str(uuid4()),
            "type": "ticket",
        },
        "different-ticket-secret-with-32-characters",
        algorithm="HS256",
    )

    with pytest.raises(jwt.PyJWTError):
        decode_ticket_token(tampered_token)


def test_shared_ticket_token_is_redacted_from_access_log() -> None:
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=(
            "127.0.0.1:50000",
            "GET",
            "/api/v1/shared-tickets/secret-token/qr",
            "1.1",
            200,
        ),
        exc_info=None,
    )

    SensitivePathFilter().filter(record)

    assert record.args[2] == "/api/v1/shared-tickets/[REDACTED]/qr"
