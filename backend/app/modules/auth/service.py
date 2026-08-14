from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.repository import add_user, get_user_by_email
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse


async def register_customer(session: AsyncSession, data: RegisterRequest) -> User:
    email = str(data.email).lower()
    if await get_user_by_email(session, email):
        raise AppError(
            "EMAIL_ALREADY_REGISTERED",
            "Já existe uma conta com este e-mail.",
            409,
        )

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        role=UserRole.CUSTOMER,
    )
    try:
        await add_user(session, user)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "EMAIL_ALREADY_REGISTERED",
            "Já existe uma conta com este e-mail.",
            409,
        ) from exc
    return user


async def authenticate(session: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(session, str(data.email).lower())
    if user is None or not verify_password(data.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "E-mail ou senha inválidos.", 401)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        user=user,
    )

