from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging
from app.modules.health.router import router as health_router


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
    application.include_router(health_router)
    return application


app = create_app()

