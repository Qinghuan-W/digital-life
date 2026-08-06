from typing import Literal, cast
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.llm.prompt_builder import (
    PersonaPromptProfile,
    build_current_identity_reminder,
    build_persona_system_prompt,
)
from app.llm.provider import LLMMessage, LLMProvider, LLMProviderError
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageSendRequest


class ChatService:
    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self.session = session
        self.provider = provider
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.settings = get_settings()

    def send_message(
        self,
        user: User,
        conversation_id: UUID,
        request: MessageSendRequest,
    ) -> tuple[Message, Message]:
        conversation = self.conversations.get_owned(conversation_id, user.id)
        if conversation is None:
            raise AppError("conversation_not_found", "对话不存在", status.HTTP_404_NOT_FOUND)

        user_message = self.messages.get_user_by_client_id(
            conversation.id,
            request.client_message_id,
        )
        if user_message is None:
            try:
                user_message = self.messages.create_user(
                    conversation_id=conversation.id,
                    content=request.content,
                    client_message_id=request.client_message_id,
                )
                self.conversations.touch(conversation, user_message.created_at)
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
                user_message = self.messages.get_user_by_client_id(
                    conversation_id,
                    request.client_message_id,
                )
                if user_message is None:
                    raise

        existing_reply = self.messages.get_assistant_reply(user_message.id)
        if existing_reply is not None:
            return user_message, existing_reply

        history = self.messages.recent_for_context(
            conversation_id,
            limit=self.settings.llm_history_limit,
        )
        persona = conversation.persona
        prompt_profile = PersonaPromptProfile(
            display_name=persona.display_name,
            relationship_label=persona.relationship_label,
            age=persona.age,
            gender_label=persona.gender_label,
            description=persona.description,
        )
        system_prompt = build_persona_system_prompt(prompt_profile)
        identity_reminder = build_current_identity_reminder(prompt_profile)
        provider_messages = [
            LLMMessage(
                role=cast(Literal["user", "assistant"], message.role),
                content=message.content,
            )
            for message in history
        ]

        # End the read transaction before waiting on an external network service.
        user_message_id = user_message.id
        self.session.rollback()
        try:
            reply_content = self.provider.generate_reply(
                system_prompt=system_prompt,
                identity_reminder=identity_reminder,
                messages=provider_messages,
            )
        except LLMProviderError as exc:
            self.session.rollback()
            raise AppError(
                "ai_service_unavailable",
                "AI 服务暂时不可用，请稍后重试。",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        conversation = self.conversations.get_owned(conversation_id, user.id)
        user_message = self.messages.get_by_id(user_message_id)
        if conversation is None or user_message is None:
            self.session.rollback()
            raise AppError("conversation_not_found", "对话不存在", status.HTTP_404_NOT_FOUND)

        existing_reply = self.messages.get_assistant_reply(user_message.id)
        if existing_reply is not None:
            return user_message, existing_reply

        try:
            assistant_message = self.messages.create_assistant(
                conversation_id=conversation.id,
                content=reply_content,
                reply_to_message_id=user_message.id,
            )
            self.conversations.touch(conversation, assistant_message.created_at)
            self.session.commit()
            return user_message, assistant_message
        except IntegrityError:
            self.session.rollback()
            user_message = self.messages.get_by_id(user_message_id)
            existing_reply = self.messages.get_assistant_reply(user_message_id)
            if user_message is not None and existing_reply is not None:
                return user_message, existing_reply
            raise
