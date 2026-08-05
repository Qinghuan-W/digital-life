from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import InvalidAccessTokenError, decode_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("invalid_access_token", "无效或缺失的访问令牌", status.HTTP_401_UNAUTHORIZED)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (InvalidAccessTokenError, ValueError, TypeError, KeyError) as exc:
        raise AppError(
            "invalid_access_token",
            "无效或过期的访问令牌",
            status.HTTP_401_UNAUTHORIZED,
        ) from exc

    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise AppError("invalid_access_token", "无效或过期的访问令牌", status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise AppError("user_inactive", "用户已停用", status.HTTP_403_FORBIDDEN)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
