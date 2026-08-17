from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


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


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    error_codes = {
        404: ("NOT_FOUND", "Recurso não encontrado."),
        405: ("METHOD_NOT_ALLOWED", "Método não permitido."),
    }
    code, message = error_codes.get(
        exc.status_code,
        ("HTTP_ERROR", "Não foi possível concluir a solicitação."),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
        headers=exc.headers,
    )
