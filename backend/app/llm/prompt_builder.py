from collections.abc import Sequence

from app.llm.provider import LLMMessage


SYSTEM_PROMPT = (
    "You are the AI assistant inside DigitalLife. Respond naturally, helpfully, and concisely. "
    "You are an AI system, not a real person. Never claim to have a physical body, a real-world "
    "location, current personal experiences, or the ability to contact third parties."
)


def build_model_input(messages: Sequence[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]
