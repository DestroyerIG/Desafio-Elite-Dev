from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.repository import get_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("INVALID_CREDENTIALS", "Autenticação necessária.", 401)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        token_role = UserRole(payload["role"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise AppError("INVALID_CREDENTIALS", "Token inválido ou expirado.", 401) from exc

    user = await get_user_by_id(session, user_id)
    if user is None or user.role != token_role:
        raise AppError("INVALID_CREDENTIALS", "Token inválido ou expirado.", 401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
RoleDependency = Callable[..., Coroutine[Any, Any, User]]


def require_roles(*allowed_roles: UserRole) -> RoleDependency:
    async def role_dependency(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise AppError("FORBIDDEN", "Você não tem permissão para esta ação.", 403)
        return current_user

    return role_dependency

