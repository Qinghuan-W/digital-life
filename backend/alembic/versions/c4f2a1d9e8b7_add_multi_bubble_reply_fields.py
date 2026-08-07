"""add multi bubble reply fields

Revision ID: c4f2a1d9e8b7
Revises: 58838a8ceb3f
Create Date: 2026-08-06 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c4f2a1d9e8b7"
down_revision: str | Sequence[str] | None = "58838a8ceb3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow one user message to own an ordered group of assistant messages."""
    op.add_column("messages", sa.Column("sequence_index", sa.SmallInteger(), nullable=True))
    op.execute(
        "UPDATE messages SET sequence_index = 0 "
        "WHERE role = 'assistant' AND reply_to_message_id IS NOT NULL"
    )
    op.drop_constraint("uq_messages_reply_to_message_id", "messages", type_="unique")
    op.drop_constraint(
        op.f("fk_messages_reply_to_message_id_messages"),
        "messages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_messages_reply_to_message_id_messages"),
        "messages",
        "messages",
        ["reply_to_message_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_messages_reply_to_message_id",
        "messages",
        ["reply_to_message_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_messages_reply_sequence",
        "messages",
        ["reply_to_message_id", "sequence_index"],
    )
    op.create_check_constraint(
        op.f("ck_messages_valid_reply_position"),
        "messages",
        "(role = 'user' AND reply_to_message_id IS NULL AND sequence_index IS NULL) OR "
        "(role = 'assistant' AND reply_to_message_id IS NOT NULL AND "
        "sequence_index BETWEEN 0 AND 3)",
    )


def downgrade() -> None:
    """Restore the original one-assistant-message-per-user-message schema."""
    op.execute(
        "DELETE FROM messages WHERE role = 'assistant' AND sequence_index IS NOT NULL "
        "AND sequence_index > 0"
    )
    op.drop_constraint(op.f("ck_messages_valid_reply_position"), "messages", type_="check")
    op.drop_constraint("uq_messages_reply_sequence", "messages", type_="unique")
    op.drop_index("ix_messages_reply_to_message_id", table_name="messages")
    op.drop_constraint(
        op.f("fk_messages_reply_to_message_id_messages"),
        "messages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_messages_reply_to_message_id_messages"),
        "messages",
        "messages",
        ["reply_to_message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_messages_reply_to_message_id",
        "messages",
        ["reply_to_message_id"],
    )
    op.drop_column("messages", "sequence_index")
