from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.persona import PersonaResponse, PersonaSummaryResponse


class DefaultConversationResponse(BaseModel):
    id: UUID
    persona_id: UUID
    title: str
    last_message_preview: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PersonaCreateResponse(BaseModel):
    persona: PersonaResponse
    conversation: DefaultConversationResponse


class ConversationListItemResponse(BaseModel):
    id: UUID
    title: str
    persona: PersonaSummaryResponse
    last_message_preview: str | None
    last_message_role: Literal["user", "assistant"] | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    id: UUID
    title: str
    persona: PersonaResponse
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime
