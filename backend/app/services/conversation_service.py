from datetime import datetime
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)

    def list_for_user(
        self,
        user: User,
    ) -> list[tuple[Conversation, str | None, str | None]]:
        return self.conversations.list_with_latest_message(user.id)

    def get_owned(self, user: User, conversation_id: UUID) -> Conversation:
        conversation = self.conversations.get_owned(conversation_id, user.id)
        if conversation is None:
            raise AppError("conversation_not_found", "对话不存在", status.HTTP_404_NOT_FOUND)
        return conversation

    def list_messages(
        self,
        user: User,
        conversation_id: UUID,
        *,
        limit: int,
        before: datetime | None,
    ) -> list[Message]:
        conversation = self.get_owned(user, conversation_id)
        return self.messages.list_for_conversation(conversation.id, limit=limit, before=before)
