from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.models.enums import UserRole


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def create_access_token(user_id: UUID, role: UserRole) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "role", "exp"]},
    )


def create_ticket_token(ticket_id: UUID, event_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "ticket_id": str(ticket_id),
        "event_id": str(event_id),
        "type": "ticket",
    }
    return jwt.encode(payload, settings.ticket_secret, algorithm=settings.jwt_algorithm)


def decode_ticket_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.ticket_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["ticket_id", "event_id", "type"]},
    )
    if payload["type"] != "ticket":
        raise jwt.InvalidTokenError("Invalid ticket token type")
    return payload


def hash_ticket_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
