from collections.abc import AsyncIterator

import httpx
import pytest

from app.database.session import get_db_session
from app.main import app


async def override_session() -> AsyncIterator[object]:
    yield object()


@pytest.mark.asyncio
async def test_request_validation_uses_standard_error_contract() -> None:
    app.dependency_overrides[get_db_session] = override_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={"name": "", "email": "inválido", "password": "123"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Os dados enviados são inválidos.",
        }
    }


@pytest.mark.asyncio
async def test_missing_credentials_use_standard_error_contract() -> None:
    app.dependency_overrides[get_db_session] = override_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": "Autenticação necessária.",
        }
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "status_code", "code"),
    [
        ("GET", "/api/v1/rota-inexistente", 404, "NOT_FOUND"),
        ("GET", "/api/v1/auth/login", 405, "METHOD_NOT_ALLOWED"),
    ],
)
async def test_http_errors_use_standard_error_contract(
    method: str,
    path: str,
    status_code: int,
    code: str,
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.request(method, path)

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code
    assert "message" in response.json()["error"]
    assert "detail" not in response.json()
