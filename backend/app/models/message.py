from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Message(TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created_at", "conversation_id", "created_at"),
        CheckConstraint("role IN ('user', 'assistant')", name="valid_role"),
        CheckConstraint("status IN ('completed', 'failed')", name="valid_status"),
        CheckConstraint(
            "(role = 'user' AND reply_to_message_id IS NULL AND sequence_index IS NULL) OR "
            "(role = 'assistant' AND reply_to_message_id IS NOT NULL AND "
            "sequence_index BETWEEN 0 AND 3)",
            name="valid_reply_position",
        ),
        UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_messages_conversation_client_message_id",
        ),
        UniqueConstraint(
            "reply_to_message_id",
            "sequence_index",
            name="uq_messages_reply_sequence",
        ),
        Index("ix_messages_reply_to_message_id", "reply_to_message_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    client_message_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    reply_to_message_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
    )
    sequence_index: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")  # noqa: F821
