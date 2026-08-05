from datetime import timedelta

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    utc_now,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.settings = get_settings()

    def register(
        self,
        request: RegisterRequest,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[User, TokenResponse]:
        if self.users.get_by_email(str(request.email)) is not None:
            raise AppError(
                "email_already_registered",
                "该邮箱已注册",
                status.HTTP_409_CONFLICT,
            )

        try:
            user = self.users.create(
                email=str(request.email),
                display_name=request.display_name,
                password_hash=hash_password(request.password),
            )
            tokens = self._issue_token_pair(
                user,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            self.session.commit()
            return user, tokens
        except IntegrityError as exc:
            self.session.rollback()
            raise AppError(
                "email_already_registered",
                "该邮箱已注册",
                status.HTTP_409_CONFLICT,
            ) from exc

    def login(
        self,
        request: LoginRequest,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[User, TokenResponse]:
        user = self.users.get_by_email(str(request.email))
        stored_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
        password_valid = verify_password(request.password, stored_hash)
        if user is None or not password_valid:
            raise AppError(
                "invalid_credentials",
                "邮箱或密码错误",
                status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            raise AppError("user_inactive", "用户已停用", status.HTTP_403_FORBIDDEN)

        tokens = self._issue_token_pair(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.commit()
        return user, tokens

    def refresh(
        self,
        raw_token: str,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenResponse:
        current = self.refresh_tokens.get_by_hash_for_update(hash_refresh_token(raw_token))
        if current is None:
            raise AppError(
                "invalid_refresh_token",
                "无效的刷新令牌",
                status.HTTP_401_UNAUTHORIZED,
            )

        now = utc_now()
        if current.revoked_at is not None:
            raise AppError(
                "refresh_token_revoked",
                "刷新令牌已失效",
                status.HTTP_401_UNAUTHORIZED,
            )
        if current.expires_at <= now:
            raise AppError(
                "refresh_token_expired",
                "刷新令牌已过期",
                status.HTTP_401_UNAUTHORIZED,
            )
        if not current.user.is_active:
            raise AppError("user_inactive", "用户已停用", status.HTTP_403_FORBIDDEN)

        new_raw_token = create_refresh_token()
        replacement = self.refresh_tokens.create(
            user_id=current.user_id,
            token_hash=hash_refresh_token(new_raw_token),
            expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.refresh_tokens.revoke(
            current,
            revoked_at=now,
            replaced_by_token_id=replacement.id,
        )
        access_token, expires_in = create_access_token(str(current.user_id))
        self.session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_token,
            expires_in=expires_in,
        )

    def logout(self, raw_token: str) -> None:
        current = self.refresh_tokens.get_by_hash_for_update(hash_refresh_token(raw_token))
        if current is None:
            raise AppError(
                "invalid_refresh_token",
                "无效的刷新令牌",
                status.HTTP_401_UNAUTHORIZED,
            )
        if current.revoked_at is None:
            self.refresh_tokens.revoke(current, revoked_at=utc_now())
        self.session.commit()

    def _issue_token_pair(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenResponse:
        access_token, expires_in = create_access_token(str(user.id))
        raw_refresh_token = create_refresh_token()
        self.refresh_tokens.create(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=utc_now() + timedelta(days=self.settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=expires_in,
        )
