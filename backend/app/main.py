from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.events.router import organizer_router, router as events_router
from app.modules.health.router import router as health_router
from app.modules.payments.router import router as payments_router
from app.modules.reservations.router import router as reservations_router
from app.modules.tickets.router import router as tickets_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.environment)

    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
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
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(catalog_router)
    application.include_router(events_router)
    application.include_router(organizer_router)
    application.include_router(reservations_router)
    application.include_router(payments_router)
    application.include_router(tickets_router)
    return application


app = create_app()
