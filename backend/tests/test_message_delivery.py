from uuid import uuid4

import pytest

from app.models.message import Message
from app.services.message_delivery import MAX_TURN_DELAY_MS, build_delivery_plan


def assistant_messages(*contents: str) -> list[Message]:
    conversation_id = uuid4()
    reply_to_message_id = uuid4()
    return [
        Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            status="completed",
            reply_to_message_id=reply_to_message_id,
            sequence_index=index,
        )
        for index, content in enumerate(contents)
    ]


@pytest.mark.parametrize(
    ("signal", "first_range", "later_range"),
    [
        ("urgent", (0, 150), (150, 350)),
        ("distressed", (50, 250), (200, 450)),
        ("affectionate", (150, 450), (300, 750)),
        ("playful", (100, 350), (250, 650)),
        ("neutral", (200, 600), (350, 800)),
        ("complex", (350, 900), (450, 1000)),
    ],
)
def test_delivery_plan_stays_within_signal_ranges(
    signal: str,
    first_range: tuple[int, int],
    later_range: tuple[int, int],
) -> None:
    plan = build_delivery_plan(
        assistant_messages("第一条" * 20, "第二条" * 20, "第三条" * 20),
        signal,
    )
    assert first_range[0] <= plan[0].delay_ms <= first_range[1]
    assert all(later_range[0] <= item.delay_ms <= later_range[1] for item in plan[1:])
    assert sum(item.delay_ms for item in plan) <= MAX_TURN_DELAY_MS


def test_urgent_first_bubble_is_faster_than_neutral_and_distressed_is_not_slow() -> None:
    messages = assistant_messages("现在看一下")
    urgent = build_delivery_plan(messages, "urgent")[0].delay_ms
    distressed = build_delivery_plan(messages, "distressed")[0].delay_ms
    neutral = build_delivery_plan(messages, "neutral")[0].delay_ms
    assert urgent < distressed < neutral


def test_invalid_signal_uses_neutral_and_reduce_motion_caps_every_delay() -> None:
    messages = assistant_messages("第一条" * 100, "第二条" * 100)
    invalid = build_delivery_plan(messages, "not-valid")
    neutral = build_delivery_plan(messages, "neutral")
    reduced = build_delivery_plan(messages, "complex", reduce_motion=True)
    assert invalid == neutral
    assert all(item.delay_ms <= 150 for item in reduced)


def test_single_bubble_plan_contains_no_follow_up_delay() -> None:
    messages = assistant_messages("只有一条")
    plan = build_delivery_plan(messages, "neutral")
    assert len(plan) == 1
    assert plan[0].message_id == messages[0].id
