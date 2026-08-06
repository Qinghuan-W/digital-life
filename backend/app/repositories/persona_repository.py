from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.persona import Persona
from app.schemas.persona import PersonaCreateRequest, PersonaUpdateRequest


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

    def get_owned(self, persona_id: UUID, user_id: UUID) -> Persona | None:
        return self.session.scalar(
            select(Persona).where(Persona.id == persona_id, Persona.user_id == user_id)
        )

    def update(self, persona: Persona, request: PersonaUpdateRequest) -> Persona:
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(persona, field, value)
        self.session.flush()
        return persona
