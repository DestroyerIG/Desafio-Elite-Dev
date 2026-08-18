import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import SHARED_TICKET_PATH


logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Erro interno. Tente novamente em instantes."


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    app_error = (
        exc
        if isinstance(exc, AppError)
        else AppError("INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE, 500)
    )
    content: dict[str, Any] = {
        "error": {"code": app_error.code, "message": app_error.message}
    }
    return JSONResponse(status_code=app_error.status_code, content=content)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Mantém o contrato quando algo falha fora do previsto.

    Sem este handler o Starlette responde `Internal Server Error` em texto puro e o
    cliente perde o `code`. A causa real vai só para o log do servidor: a resposta
    nunca carrega mensagem de exceção, stack trace ou nome de tabela.
    """
    path = SHARED_TICKET_PATH.sub(r"\1[REDACTED]", request.url.path)
    logger.error(
        "Falha não tratada em %s %s", request.method, path, exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": INTERNAL_ERROR_MESSAGE}},
    )


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
