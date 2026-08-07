import os
from collections.abc import Generator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


os.environ["APP_ENV"] = "test"
postgres_bin = r"C:\Program Files\PostgreSQL\17\bin"
os.environ["PATH"] = f"{postgres_bin};{os.environ.get('PATH', '')}"

from app.core.database import SessionLocal, engine  # noqa: E402
from app.dependencies.llm import get_llm_provider  # noqa: E402
from app.llm.provider import GeneratedAssistantTurn, LLMMessage, LLMProviderError  # noqa: E402
from app.main import app  # noqa: E402


if not str(engine.url).endswith("/digitallife_test"):
    raise RuntimeError("Tests must use the digitallife_test database.")


@pytest.fixture(autouse=True)
def clean_test_database() -> Generator[None, None, None]:
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE messages, conversations, personas, refresh_tokens, users CASCADE")
        )
    yield


@dataclass(frozen=True)
class FakeLLMCall:
    system_prompt: str
    identity_reminder: str
    messages: list[LLMMessage]


class FakeLLMProvider:
    def __init__(self) -> None:
        self.reply = "刚吃完，正躺着歇会儿。"
        self.replies: list[str] | None = None
        self.conversation_signal = "neutral"
        self.fail = False
        self.calls: list[FakeLLMCall] = []

    def generate_reply(
        self,
        *,
        system_prompt: str,
        identity_reminder: str,
        messages: list[LLMMessage],
    ) -> GeneratedAssistantTurn:
        self.calls.append(
            FakeLLMCall(
                system_prompt=system_prompt,
                identity_reminder=identity_reminder,
                messages=list(messages),
            )
        )
        if self.fail:
            raise LLMProviderError("fake provider failure")
        return GeneratedAssistantTurn(
            messages=self.replies or [self.reply],
            conversation_signal=self.conversation_signal,
        )


@pytest.fixture
def fake_llm() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def client(fake_llm: FakeLLMProvider) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_llm_provider, None)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
