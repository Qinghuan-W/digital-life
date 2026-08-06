from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.persona import Persona
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.persona import PersonaCreateRequest


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
