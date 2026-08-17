from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    http_exception_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.events.router import organizer_router, router as events_router
from app.modules.gate.router import router as gate_router
from app.modules.health.router import router as health_router
from app.modules.payments.router import router as payments_router
from app.modules.reservations.router import router as reservations_router
from app.modules.seats.realtime import seat_map_runtime
from app.modules.seats.router import router as seats_router
from app.modules.tickets.router import router as tickets_router


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    await seat_map_runtime.start()
    try:
        yield
    finally:
        await seat_map_runtime.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.environment)
    settings.upload_directory.mkdir(parents=True, exist_ok=True)

    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.frontend_url).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(catalog_router)
    application.include_router(events_router)
    application.include_router(organizer_router)
    application.include_router(reservations_router)
    application.include_router(seats_router)
    application.include_router(payments_router)
    application.include_router(tickets_router)
    application.include_router(gate_router)
    application.mount(
        "/uploads",
        StaticFiles(directory=settings.upload_directory),
        name="uploads",
    )
    return application


app = create_app()
