from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import utc_now
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: UUID, persona_id: UUID, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, persona_id=persona_id, title=title)
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def get_owned(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        statement = (
            select(Conversation)
            .options(joinedload(Conversation.persona))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return self.session.scalar(statement)

    def get_owned_by_persona(self, persona_id: UUID, user_id: UUID) -> Conversation | None:
        return self.session.scalar(
            select(Conversation).where(
                Conversation.persona_id == persona_id,
                Conversation.user_id == user_id,
            )
        )

    def list_with_latest_message(
        self,
        user_id: UUID,
    ) -> list[tuple[Conversation, str | None, str | None]]:
        latest_content = (
            select(Message.content)
            .where(Message.conversation_id == Conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_role = (
            select(Message.role)
            .where(Message.conversation_id == Conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
            .scalar_subquery()
        )
        statement = (
            select(Conversation, latest_content.label("latest_content"), latest_role.label("latest_role"))
            .options(joinedload(Conversation.persona))
            .where(Conversation.user_id == user_id)
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.created_at.desc(),
            )
        )
        return [(row[0], row[1], row[2]) for row in self.session.execute(statement).all()]

    def touch(self, conversation: Conversation, message_at: datetime) -> None:
        conversation.last_message_at = message_at
        conversation.updated_at = utc_now()
        self.session.flush()
