from dataclasses import dataclass
from typing import Literal, Protocol, Sequence


@dataclass(frozen=True)
class LLMMessage:
    role: Literal["user", "assistant"]
    content: str


class LLMProvider(Protocol):
    def generate_reply(self, messages: Sequence[LLMMessage]) -> str: ...


class LLMProviderError(Exception):
    pass
