from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.schemas.conversation import DefaultConversationResponse, PersonaCreateResponse
from app.schemas.error import ErrorResponse
from app.schemas.persona import PersonaCreateRequest, PersonaResponse, PersonaUpdateRequest
from app.services.persona_service import PersonaService


router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post(
    "",
    response_model=PersonaCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Persona and its default conversation",
    responses={422: {"model": ErrorResponse, "description": "Validation error"}},
)
def create_persona(
    payload: PersonaCreateRequest,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> PersonaCreateResponse:
    persona, conversation = PersonaService(session).create_with_default_conversation(user, payload)
    return PersonaCreateResponse(
        persona=PersonaResponse.model_validate(persona),
        conversation=DefaultConversationResponse(
            id=conversation.id,
            persona_id=conversation.persona_id,
            title=conversation.title,
            last_message_preview=None,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        ),
    )


@router.get("", response_model=list[PersonaResponse], summary="List current user's Personas")
def list_personas(
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> list[PersonaResponse]:
    return [
        PersonaResponse.model_validate(persona)
        for persona in PersonaService(session).list_for_user(user)
    ]


@router.patch(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Update a Persona",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def update_persona(
    persona_id: UUID,
    payload: PersonaUpdateRequest,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> PersonaResponse:
    persona = PersonaService(session).update(user, persona_id, payload)
    return PersonaResponse.model_validate(persona)
