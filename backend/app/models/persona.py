from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, SmallInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Persona(TimestampMixin, Base):
    __tablename__ = "personas"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship_label: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    gender_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        back_populates="persona",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
