from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
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
        )
