from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the current profile",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid access token"},
        403: {"model": ErrorResponse, "description": "Inactive user"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def update_current_user(
    payload: UserUpdateRequest,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    updated_user = UserRepository(session).update_display_name(user, payload.display_name)
    session.commit()
    return UserResponse.model_validate(updated_user)
