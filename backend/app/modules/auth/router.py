from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import authenticate, register_customer


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(data: RegisterRequest, session: DatabaseSession) -> UserResponse:
    return UserResponse.model_validate(await register_customer(session, data))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: DatabaseSession) -> TokenResponse:
    return await authenticate(session, data)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)

