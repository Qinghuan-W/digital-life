from dataclasses import dataclass
from typing import Any, Literal, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_ASSISTANT_MESSAGE_LENGTH = 4000
MAX_ASSISTANT_TURN_LENGTH = 8000
ConversationSignal = Literal[
    "urgent",
    "distressed",
    "affectionate",
    "playful",
    "neutral",
    "complex",
]
VALID_CONVERSATION_SIGNALS = {
    "urgent",
    "distressed",
    "affectionate",
    "playful",
    "neutral",
    "complex",
}


@dataclass(frozen=True)
class LLMMessage:
    role: Literal["user", "assistant"]
    content: str


class GeneratedAssistantTurn(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    messages: list[str] = Field(min_length=1, max_length=4)
    conversation_signal: ConversationSignal = "neutral"

    @field_validator("messages", mode="before")
    @classmethod
    def normalize_messages(cls, messages: Any) -> list[str]:
        if not isinstance(messages, list):
            raise ValueError("Assistant messages must be a list")
        normalized: list[str] = []
        for message in messages:
            if not isinstance(message, str):
                raise ValueError("Assistant messages must be strings")
            content = message.strip()
            if not content:
                continue
            if len(content) > MAX_ASSISTANT_MESSAGE_LENGTH:
                raise ValueError("An assistant message is too long")
            normalized.append(content)
        if not normalized:
            raise ValueError("Assistant messages cannot all be blank")
        if len(normalized) > 4:
            raise ValueError("An assistant turn cannot contain more than four messages")
        if sum(len(message) for message in normalized) > MAX_ASSISTANT_TURN_LENGTH:
            raise ValueError("The assistant turn is too long")
        return normalized

    @field_validator("conversation_signal", mode="before")
    @classmethod
    def normalize_conversation_signal(cls, value: Any) -> str:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in VALID_CONVERSATION_SIGNALS:
                return normalized
        return "neutral"


class LLMProvider(Protocol):
    def generate_reply(
        self,
        *,
        system_prompt: str,
        identity_reminder: str,
        messages: Sequence[LLMMessage],
    ) -> GeneratedAssistantTurn: ...


class LLMProviderError(Exception):
    def __init__(
        self,
        message: str = "The model provider request failed",
        *,
        provider_operation: str | None = None,
        api_mode: str | None = None,
        model: str | None = None,
        http_status: int | None = None,
        provider_error_type: str | None = None,
        provider_error_code: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider_operation = provider_operation
        self.api_mode = api_mode
        self.model = model
        self.http_status = http_status
        self.provider_error_type = provider_error_type
        self.provider_error_code = provider_error_code
        self.retryable = retryable
