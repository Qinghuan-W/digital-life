from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.schemas.error import ErrorResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])
VALIDATION_RESPONSE = {422: {"model": ErrorResponse, "description": "Validation error"}}


def request_metadata(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        **VALIDATION_RESPONSE,
    },
)
def register(
    payload: RegisterRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    user_agent, ip_address = request_metadata(request)
    user, tokens = AuthService(session).register(
        payload,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return AuthResponse(user=UserResponse.model_validate(user), **tokens.model_dump())


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email and password",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Inactive user"},
        **VALIDATION_RESPONSE,
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    user_agent, ip_address = request_metadata(request)
    user, tokens = AuthService(session).login(
        payload,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return AuthResponse(user=UserResponse.model_validate(user), **tokens.model_dump())


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate a refresh token",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid, expired, or revoked refresh token"},
        403: {"model": ErrorResponse, "description": "Inactive user"},
        **VALIDATION_RESPONSE,
    },
)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user_agent, ip_address = request_metadata(request)
    return AuthService(session).refresh(
        payload.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid access token"},
        403: {"model": ErrorResponse, "description": "Inactive user"},
    },
)
def current_user(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        **VALIDATION_RESPONSE,
    },
)
def logout(
    payload: LogoutRequest,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    AuthService(session).logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
