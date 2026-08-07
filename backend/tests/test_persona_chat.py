from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.persona import Persona
from app.models.user import User
from app.repositories.message_repository import MessageRepository
from app.services.persona_service import PersonaService
from app.schemas.persona import PersonaCreateRequest
from conftest import FakeLLMProvider


def register_user(
    client: TestClient,
    *,
    email: str = "persona@example.com",
    display_name: str = "Persona Owner",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": display_name, "password": "secure-password"},
    )
    assert response.status_code == 201
    return response.json()


def headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def create_persona(
    client: TestClient,
    auth: dict,
    *,
    name: str = "小雨",
    relationship: str = "朋友",
) -> dict:
    response = client.post(
        "/api/v1/personas",
        headers=headers(auth),
        json={
            "display_name": name,
            "relationship_label": relationship,
            "age": 22,
            "gender_label": "女",
            "description": "大学时期认识的朋友",
        },
    )
    assert response.status_code == 201
    return response.json()


def send_message(
    client: TestClient,
    auth: dict,
    conversation_id: str,
    *,
    content: str = "你好",
    client_message_id: str | None = None,
):
    return client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
        json={"content": content, "client_message_id": client_message_id or str(uuid4())},
    )


def test_create_persona_normalizes_and_returns_default_conversation(client: TestClient) -> None:
    auth = register_user(client)
    response = client.post(
        "/api/v1/personas",
        headers=headers(auth),
        json={"display_name": "  小雨  ", "relationship_label": "  朋友  ", "age": 22},
    )
    body = response.json()
    assert response.status_code == 201
    assert body["persona"]["display_name"] == "小雨"
    assert body["persona"]["relationship_label"] == "朋友"
    assert body["conversation"]["title"] == "小雨"
    assert body["conversation"]["persona_id"] == body["persona"]["id"]


def test_create_persona_persists_persona_and_conversation(
    client: TestClient,
    db_session: Session,
) -> None:
    auth = register_user(client)
    body = create_persona(client, auth)
    persona = db_session.get(Persona, body["persona"]["id"])
    conversation = db_session.get(Conversation, body["conversation"]["id"])
    assert persona is not None and conversation is not None
    assert conversation.persona_id == persona.id
    assert conversation.user_id == persona.user_id


def test_persona_and_conversation_creation_rolls_back_together(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = register_user(client)
    user = db_session.get(User, auth["user"]["id"])
    assert user is not None
    service = PersonaService(db_session)

    def fail_create(**_kwargs):
        raise RuntimeError("forced conversation failure")

    monkeypatch.setattr(service.conversations, "create", fail_create)
    with pytest.raises(RuntimeError):
        service.create_with_default_conversation(
            user,
            PersonaCreateRequest(display_name="小雨", relationship_label="朋友"),
        )
    assert db_session.scalar(select(func.count()).select_from(Persona)) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [("display_name", "   "), ("relationship_label", "  ")],
)
def test_required_persona_fields_reject_blank(
    client: TestClient,
    field: str,
    value: str,
) -> None:
    auth = register_user(client)
    payload = {"display_name": "小雨", "relationship_label": "朋友", field: value}
    response = client.post("/api/v1/personas", headers=headers(auth), json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


@pytest.mark.parametrize("age", [0, 151])
def test_persona_age_out_of_range_is_rejected(client: TestClient, age: int) -> None:
    auth = register_user(client)
    response = client.post(
        "/api/v1/personas",
        headers=headers(auth),
        json={"display_name": "小雨", "relationship_label": "朋友", "age": age},
    )
    assert response.status_code == 422


def test_optional_blank_persona_fields_become_null(client: TestClient) -> None:
    auth = register_user(client)
    response = client.post(
        "/api/v1/personas",
        headers=headers(auth),
        json={
            "display_name": "小雨",
            "relationship_label": "朋友",
            "gender_label": "   ",
            "description": "  ",
        },
    )
    assert response.status_code == 201
    assert response.json()["persona"]["gender_label"] is None
    assert response.json()["persona"]["description"] is None


def test_persona_list_only_contains_current_users_data(client: TestClient) -> None:
    first = register_user(client, email="first@example.com")
    second = register_user(client, email="second@example.com")
    create_persona(client, first, name="First Persona")
    create_persona(client, second, name="Second Persona")
    response = client.get("/api/v1/personas", headers=headers(first))
    assert response.status_code == 200
    assert [item["display_name"] for item in response.json()] == ["First Persona"]


def test_conversation_list_only_contains_current_users_data(client: TestClient) -> None:
    first = register_user(client, email="first@example.com")
    second = register_user(client, email="second@example.com")
    create_persona(client, first, name="First Persona")
    create_persona(client, second, name="Second Persona")
    response = client.get("/api/v1/conversations", headers=headers(first))
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["First Persona"]


def test_non_owner_cannot_get_conversation(client: TestClient) -> None:
    owner = register_user(client, email="owner@example.com")
    other = register_user(client, email="other@example.com")
    conversation_id = create_persona(client, owner)["conversation"]["id"]
    response = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers(other))
    assert response.status_code == 404
    assert response.json()["error"] == "conversation_not_found"


def test_non_owner_cannot_get_messages(client: TestClient) -> None:
    owner = register_user(client, email="owner@example.com")
    other = register_user(client, email="other@example.com")
    conversation_id = create_persona(client, owner)["conversation"]["id"]
    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(other),
    )
    assert response.status_code == 404


def test_non_owner_cannot_send_message(client: TestClient) -> None:
    owner = register_user(client, email="owner@example.com")
    other = register_user(client, email="other@example.com")
    conversation_id = create_persona(client, owner)["conversation"]["id"]
    response = send_message(client, other, conversation_id)
    assert response.status_code == 404


def test_empty_conversation_has_null_preview(client: TestClient) -> None:
    auth = register_user(client)
    create_persona(client, auth)
    item = client.get("/api/v1/conversations", headers=headers(auth)).json()[0]
    assert item["last_message_preview"] is None
    assert item["last_message_at"] is None


def test_conversations_sort_by_latest_message_then_creation(
    client: TestClient,
    db_session: Session,
) -> None:
    auth = register_user(client)
    first = create_persona(client, auth, name="First")
    second = create_persona(client, auth, name="Second")
    assert send_message(client, auth, first["conversation"]["id"]).status_code == 200
    rows = client.get("/api/v1/conversations", headers=headers(auth)).json()
    assert [item["title"] for item in rows] == ["First", "Second"]
    first_conversation = db_session.get(Conversation, first["conversation"]["id"])
    second_conversation = db_session.get(Conversation, second["conversation"]["id"])
    assert first_conversation is not None and second_conversation is not None
    assert first_conversation.last_message_at is not None


def test_conversation_preview_uses_latest_message_and_truncates(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    long_reply = "回" * 140
    fake_llm.reply = long_reply
    assert send_message(client, auth, conversation_id).status_code == 200
    item = client.get("/api/v1/conversations", headers=headers(auth)).json()[0]
    assert item["last_message_preview"] == "回" * 100
    assert item["last_message_role"] == "assistant"


def test_conversation_detail_includes_persona(client: TestClient) -> None:
    auth = register_user(client)
    created = create_persona(client, auth)
    response = client.get(
        f"/api/v1/conversations/{created['conversation']['id']}",
        headers=headers(auth),
    )
    assert response.status_code == 200
    assert response.json()["persona"]["relationship_label"] == "朋友"


def test_send_message_returns_and_persists_both_messages(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    response = send_message(client, auth, conversation_id, content="今天怎么样？")
    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["content"] == "今天怎么样？"
    assert [message["content"] for message in body["assistant_messages"]] == [fake_llm.reply]
    assert [item["message_id"] for item in body["delivery_plan"]] == [
        body["assistant_messages"][0]["id"]
    ]
    assert body["user_message"]["reply_to_message_id"] is None
    assert body["user_message"]["sequence_index"] is None
    assert body["assistant_messages"][0]["reply_to_message_id"] == body["user_message"]["id"]
    assert body["assistant_messages"][0]["sequence_index"] == 0
    stored = list(
        db_session.scalars(
            select(Message)
            .where(Message.conversation_id == UUID(conversation_id))
            .order_by(Message.created_at)
        )
    )
    assert [message.role for message in stored] == ["user", "assistant"]


@pytest.mark.parametrize(
    "replies",
    [["一条回复"], ["第一条", "第二条"], ["一", "二", "三", "四"]],
)
def test_provider_turn_persists_one_to_four_ordered_assistant_messages(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
    replies: list[str],
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = replies
    response = send_message(client, auth, conversation_id, content="说点什么")
    assert response.status_code == 200
    body = response.json()
    assistant_messages = body["assistant_messages"]
    assert [message["content"] for message in assistant_messages] == replies
    assert [message["sequence_index"] for message in assistant_messages] == list(
        range(len(replies))
    )
    assert all(
        message["reply_to_message_id"] == body["user_message"]["id"]
        for message in assistant_messages
    )
    assert len(fake_llm.calls) == 1
    assert [item["message_id"] for item in body["delivery_plan"]] == [
        message["id"] for message in assistant_messages
    ]

    stored = list(
        db_session.scalars(
            select(Message)
            .where(Message.role == "assistant")
            .order_by(Message.sequence_index)
        )
    )
    assert [message.content for message in stored] == replies


def test_multi_message_retry_returns_existing_complete_turn_without_provider_call(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    client_message_id = str(uuid4())
    fake_llm.replies = ["第一条", "第二条", "第三条"]
    first = send_message(
        client,
        auth,
        conversation_id,
        client_message_id=client_message_id,
    )
    second = send_message(
        client,
        auth,
        conversation_id,
        client_message_id=client_message_id,
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["user_message"]["id"] == second.json()["user_message"]["id"]
    assert [message["id"] for message in first.json()["assistant_messages"]] == [
        message["id"] for message in second.json()["assistant_messages"]
    ]
    assert second.json()["delivery_plan"] == []
    assert len(fake_llm.calls) == 1
    assert db_session.scalar(select(func.count()).select_from(Message)) == 4


def test_conversation_preview_uses_last_assistant_bubble(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = ["前一个气泡", "最后一个气泡"]
    assert send_message(client, auth, conversation_id).status_code == 200
    item = client.get("/api/v1/conversations", headers=headers(auth)).json()[0]
    assert item["last_message_preview"] == "最后一个气泡"
    assert item["last_message_role"] == "assistant"


def test_delivery_plan_and_conversation_signal_are_not_in_message_history(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = ["第一条", "第二条"]
    fake_llm.conversation_signal = "playful"
    sent = send_message(client, auth, conversation_id)
    assert sent.status_code == 200
    assert len(sent.json()["delivery_plan"]) == 2
    history = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
    ).json()
    assert all("delivery_plan" not in message for message in history)
    assert all("conversation_signal" not in message for message in history)


def test_multi_message_history_is_ordered_and_exposes_reply_metadata(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = ["先说这个", "再补一句", "最后一句"]
    response = send_message(client, auth, conversation_id, content="开始")
    assert response.status_code == 200
    history = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
    ).json()
    assert [message["content"] for message in history] == [
        "开始",
        "先说这个",
        "再补一句",
        "最后一句",
    ]
    assert [message["sequence_index"] for message in history] == [None, 0, 1, 2]


def test_reply_sequence_unique_constraint_prevents_duplicate_bubble(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = ["唯一气泡"]
    body = send_message(client, auth, conversation_id).json()
    duplicate = Message(
        conversation_id=UUID(conversation_id),
        role="assistant",
        content="重复气泡",
        status="completed",
        reply_to_message_id=UUID(body["user_message"]["id"]),
        sequence_index=0,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_failure_rolls_back_entire_assistant_turn(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.replies = ["第一条", "第二条"]

    def fail_after_partial_add(
        repository: MessageRepository,
        *,
        conversation_id: UUID,
        contents: list[str],
        reply_to_message_id: UUID,
    ) -> list[Message]:
        partial = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=contents[0],
            status="completed",
            reply_to_message_id=reply_to_message_id,
            sequence_index=0,
        )
        repository.session.add(partial)
        repository.session.flush()
        raise RuntimeError("forced atomic save failure")

    monkeypatch.setattr(MessageRepository, "create_assistants", fail_after_partial_add)
    response = send_message(client, auth, conversation_id)
    assert response.status_code == 500
    db_session.expire_all()
    stored = list(db_session.scalars(select(Message)))
    assert len(stored) == 1
    assert stored[0].role == "user"


def test_prompt_and_developer_reminder_are_not_persisted(
    client: TestClient,
    db_session: Session,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    assert send_message(client, auth, conversation_id, content="普通内容").status_code == 200
    contents = list(db_session.scalars(select(Message.content)))
    assert all("[Private Chat Mode]" not in content for content in contents)
    assert all("[Current Identity" not in content for content in contents)


@pytest.mark.parametrize("content", ["   ", "x" * 4001])
def test_invalid_message_content_is_rejected(client: TestClient, content: str) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    response = send_message(client, auth, conversation_id, content=content)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_send_updates_last_message_time(
    client: TestClient,
    db_session: Session,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    assert send_message(client, auth, conversation_id).status_code == 200
    db_session.expire_all()
    conversation = db_session.get(Conversation, UUID(conversation_id))
    assert conversation is not None and conversation.last_message_at is not None


def test_same_client_message_id_is_idempotent(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    message_id = str(uuid4())
    first = send_message(client, auth, conversation_id, client_message_id=message_id)
    second = send_message(client, auth, conversation_id, client_message_id=message_id)
    assert first.status_code == second.status_code == 200
    count = db_session.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == UUID(conversation_id))
    )
    assert count == 2
    assert len(fake_llm.calls) == 1


def test_llm_failure_returns_safe_error_and_keeps_only_user_message(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.fail = True
    response = send_message(client, auth, conversation_id)
    assert response.status_code == 503
    assert response.json() == {
        "error": "ai_service_unavailable",
        "message": "AI 服务暂时不可用，请稍后重试。",
    }
    stored = list(db_session.scalars(select(Message)))
    assert len(stored) == 1
    assert stored[0].role == "user"


def test_llm_failure_does_not_poison_database_session(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.fail = True
    assert send_message(client, auth, conversation_id).status_code == 503
    response = client.get("/api/v1/conversations", headers=headers(auth))
    assert response.status_code == 200


def test_retry_after_llm_failure_reuses_user_message(
    client: TestClient,
    db_session: Session,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    message_id = str(uuid4())
    fake_llm.fail = True
    assert send_message(client, auth, conversation_id, client_message_id=message_id).status_code == 503
    fake_llm.fail = False
    assert send_message(client, auth, conversation_id, client_message_id=message_id).status_code == 200
    assert db_session.scalar(select(func.count()).select_from(Message)) == 2


def test_message_history_is_chronological(client: TestClient, fake_llm: FakeLLMProvider) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    fake_llm.reply = "第一条回复"
    send_message(client, auth, conversation_id, content="第一条")
    fake_llm.reply = "第二条回复"
    send_message(client, auth, conversation_id, content="第二条")
    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
    )
    assert [item["content"] for item in response.json()] == [
        "第一条",
        "第一条回复",
        "第二条",
        "第二条回复",
    ]


def test_message_history_supports_limit_and_before(client: TestClient) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    send_message(client, auth, conversation_id)
    all_messages = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
    ).json()
    limited = client.get(
        f"/api/v1/conversations/{conversation_id}/messages?limit=1",
        headers=headers(auth),
    ).json()
    before = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers(auth),
        params={"before": all_messages[-1]["created_at"]},
    ).json()
    assert len(limited) == 1
    assert [item["id"] for item in before] == [all_messages[0]["id"]]


def test_persona_profile_is_passed_to_provider_as_dynamic_system_prompt(
    client: TestClient,
    fake_llm: FakeLLMProvider,
) -> None:
    auth = register_user(client)
    created = create_persona(client, auth, name="动态 Prompt 的名字", relationship="同事")
    send_message(client, auth, created["conversation"]["id"], content="普通消息")
    call = fake_llm.calls[0]
    assert "动态 Prompt 的名字" in call.system_prompt
    assert "同事" in call.system_prompt
    assert [message.content for message in call.messages].count("普通消息") == 1


def test_deleting_user_cascades_persona_conversation_and_messages(
    client: TestClient,
    db_session: Session,
) -> None:
    auth = register_user(client)
    conversation_id = create_persona(client, auth)["conversation"]["id"]
    send_message(client, auth, conversation_id)
    user = db_session.get(User, auth["user"]["id"])
    assert user is not None
    db_session.delete(user)
    db_session.commit()
    assert db_session.scalar(select(func.count()).select_from(Persona)) == 0
    assert db_session.scalar(select(func.count()).select_from(Conversation)) == 0
    assert db_session.scalar(select(func.count()).select_from(Message)) == 0
