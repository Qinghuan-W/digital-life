from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.persona import Persona
from app.schemas.persona import PersonaCreateRequest


class PersonaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: UUID, request: PersonaCreateRequest) -> Persona:
        persona = Persona(user_id=user_id, **request.model_dump())
        self.session.add(persona)
        self.session.flush()
        return persona

    def list_for_user(self, user_id: UUID) -> list[Persona]:
        statement = (
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.created_at.desc())
        )
        return list(self.session.scalars(statement))
