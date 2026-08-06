from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.dependencies.llm import CurrentLLMProvider
from app.schemas.conversation import ConversationDetailResponse, ConversationListItemResponse
from app.schemas.error import ErrorResponse
from app.schemas.message import MessageResponse, MessageSendRequest, MessageSendResponse
from app.schemas.persona import PersonaResponse, PersonaSummaryResponse
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService


router = APIRouter(prefix="/conversations", tags=["Conversations"])
NOT_FOUND_RESPONSE = {404: {"model": ErrorResponse, "description": "Conversation not found"}}


@router.get("", response_model=list[ConversationListItemResponse], summary="List conversations")
def list_conversations(
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> list[ConversationListItemResponse]:
    rows = ConversationService(session).list_for_user(user)
    return [
        ConversationListItemResponse(
            id=conversation.id,
            title=conversation.title,
            persona=PersonaSummaryResponse.model_validate(conversation.persona),
            last_message_preview=(preview[:100] if preview else None),
            last_message_role=role,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation, preview, role in rows
    ]


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details",
    responses=NOT_FOUND_RESPONSE,
)
def get_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> ConversationDetailResponse:
    conversation = ConversationService(session).get_owned(user, conversation_id)
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        persona=PersonaResponse.model_validate(conversation.persona),
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="Get conversation message history",
    responses=NOT_FOUND_RESPONSE,
)
def list_messages(
    conversation_id: UUID,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before: datetime | None = None,
) -> list[MessageResponse]:
    messages = ConversationService(session).list_messages(
        user,
        conversation_id,
        limit=limit,
        before=before,
    )
    return [MessageResponse.model_validate(message) for message in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageSendResponse,
    summary="Send a message and generate an AI reply",
    responses={
        **NOT_FOUND_RESPONSE,
        503: {"model": ErrorResponse, "description": "AI service unavailable"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def send_message(
    conversation_id: UUID,
    payload: MessageSendRequest,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
    provider: CurrentLLMProvider,
) -> MessageSendResponse:
    user_message, assistant_message = ChatService(session, provider).send_message(
        user,
        conversation_id,
        payload,
    )
    return MessageSendResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )
