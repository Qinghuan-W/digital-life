from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import utc_now
from app.models.conversation import Conversation
from app.models.persona import Persona
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.persona import PersonaCreateRequest, PersonaUpdateRequest


class PersonaService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.personas = PersonaRepository(session)
        self.conversations = ConversationRepository(session)

    def create_with_default_conversation(
        self,
        user: User,
        request: PersonaCreateRequest,
    ) -> tuple[Persona, Conversation]:
        try:
            persona = self.personas.create(user_id=user.id, request=request)
            conversation = self.conversations.create(
                user_id=user.id,
                persona_id=persona.id,
                title=persona.display_name,
            )
            self.session.commit()
            return persona, conversation
        except Exception:
            self.session.rollback()
            raise

    def list_for_user(self, user: User) -> list[Persona]:
        return self.personas.list_for_user(user.id)

    def update(self, user: User, persona_id: UUID, request: PersonaUpdateRequest) -> Persona:
        persona = self.personas.get_owned(persona_id, user.id)
        if persona is None:
            raise AppError("persona_not_found", "Persona 不存在", status.HTTP_404_NOT_FOUND)
        try:
            persona = self.personas.update(persona, request)
            if "display_name" in request.model_fields_set:
                conversation = self.conversations.get_owned_by_persona(persona.id, user.id)
                if conversation is None:
                    raise AppError(
                        "conversation_not_found",
                        "对话不存在",
                        status.HTTP_404_NOT_FOUND,
                    )
                conversation.title = persona.display_name
                conversation.updated_at = utc_now()
            persona.updated_at = utc_now()
            self.session.commit()
            return persona
        except Exception:
            self.session.rollback()
            raise
