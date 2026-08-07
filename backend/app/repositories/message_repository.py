from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, message_id: UUID) -> Message | None:
        return self.session.get(Message, message_id)

    def get_user_by_client_id(
        self,
        conversation_id: UUID,
        client_message_id: UUID,
    ) -> Message | None:
        statement = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.client_message_id == client_message_id,
            Message.role == "user",
        )
        return self.session.scalar(statement)

    def get_assistant_replies(self, user_message_id: UUID) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.reply_to_message_id == user_message_id,
                Message.role == "assistant",
            )
            .order_by(Message.sequence_index.asc(), Message.created_at.asc(), Message.id.asc())
        )
        return list(self.session.scalars(statement))

    def create_user(
        self,
        *,
        conversation_id: UUID,
        content: str,
        client_message_id: UUID,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            status="completed",
            client_message_id=client_message_id,
        )
        self.session.add(message)
        self.session.flush()
        return message

    def create_assistants(
        self,
        *,
        conversation_id: UUID,
        contents: list[str],
        reply_to_message_id: UUID,
    ) -> list[Message]:
        messages = [
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                status="completed",
                reply_to_message_id=reply_to_message_id,
                sequence_index=sequence_index,
            )
            for sequence_index, content in enumerate(contents)
        ]
        self.session.add_all(messages)
        self.session.flush()
        return messages

    def list_for_conversation(
        self,
        conversation_id: UUID,
        *,
        limit: int,
        before: datetime | None,
    ) -> list[Message]:
        statement = select(Message).where(Message.conversation_id == conversation_id)
        if before is not None:
            statement = statement.where(Message.created_at < before)
        statement = statement.order_by(
            Message.created_at.desc(),
            Message.sequence_index.desc().nullslast(),
            Message.id.desc(),
        ).limit(limit)
        return list(reversed(list(self.session.scalars(statement))))

    def recent_for_context(self, conversation_id: UUID, *, limit: int) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.status == "completed",
            )
            .order_by(
                Message.created_at.desc(),
                Message.sequence_index.desc().nullslast(),
                Message.id.desc(),
            )
            .limit(limit)
        )
        return list(reversed(list(self.session.scalars(statement))))
