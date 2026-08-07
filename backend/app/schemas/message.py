from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageSendRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    client_message_id: UUID

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("消息内容不能为空")
        return normalized


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant"]
    content: str
    status: Literal["completed", "failed"]
    client_message_id: UUID | None
    reply_to_message_id: UUID | None
    sequence_index: int | None
    created_at: datetime
    updated_at: datetime


class MessageDeliveryPlanItemResponse(BaseModel):
    message_id: UUID
    delay_ms: int = Field(ge=0, le=3000)


class MessageSendResponse(BaseModel):
    user_message: MessageResponse
    assistant_messages: list[MessageResponse]
    delivery_plan: list[MessageDeliveryPlanItemResponse]
