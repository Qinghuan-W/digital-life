from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.llm.provider import VALID_CONVERSATION_SIGNALS, ConversationSignal
from app.models.message import Message


MAX_TURN_DELAY_MS = 3000
_DELAY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "urgent": ((0, 150), (150, 350)),
    "distressed": ((50, 250), (200, 450)),
    "affectionate": ((150, 450), (300, 750)),
    "playful": ((100, 350), (250, 650)),
    "neutral": ((200, 600), (350, 800)),
    "complex": ((350, 900), (450, 1000)),
}


@dataclass(frozen=True)
class DeliveryPlanItem:
    message_id: UUID
    delay_ms: int


def build_delivery_plan(
    assistant_messages: Sequence[Message],
    conversation_signal: ConversationSignal | str,
    *,
    reduce_motion: bool = False,
) -> list[DeliveryPlanItem]:
    """Build deterministic, ephemeral delays; no value is persisted."""
    signal = (
        conversation_signal
        if conversation_signal in VALID_CONVERSATION_SIGNALS
        else "neutral"
    )
    first_bounds, later_bounds = _DELAY_BOUNDS[signal]
    planned: list[DeliveryPlanItem] = []
    elapsed = 0

    for index, message in enumerate(assistant_messages):
        minimum, maximum = first_bounds if index == 0 else later_bounds
        previous_length = len(assistant_messages[index - 1].content) if index > 0 else 0
        conversational_length = min(160, previous_length + len(message.content))
        delay = minimum + min(maximum - minimum, conversational_length * 4)

        remaining_count = len(assistant_messages) - index - 1
        remaining_minimum = remaining_count * later_bounds[0]
        delay = min(delay, MAX_TURN_DELAY_MS - elapsed - remaining_minimum)
        delay = max(minimum, delay)
        if reduce_motion:
            delay = min(150, delay // 5)

        planned.append(DeliveryPlanItem(message_id=message.id, delay_ms=delay))
        elapsed += delay

    return planned
