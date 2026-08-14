from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    app_error = exc if isinstance(exc, AppError) else AppError("INTERNAL_ERROR", "Erro interno.", 500)
    content: dict[str, Any] = {
        "error": {"code": app_error.code, "message": app_error.message}
    }
    return JSONResponse(status_code=app_error.status_code, content=content)


async def validation_error_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Os dados enviados são inválidos.",
            }
        },
    )
