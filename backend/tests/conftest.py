import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


os.environ["APP_ENV"] = "test"
postgres_bin = r"C:\Program Files\PostgreSQL\17\bin"
os.environ["PATH"] = f"{postgres_bin};{os.environ.get('PATH', '')}"

from app.core.database import SessionLocal, engine  # noqa: E402
from app.dependencies.llm import get_llm_provider  # noqa: E402
from app.llm.provider import LLMMessage, LLMProviderError  # noqa: E402
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


class FakeLLMProvider:
    def __init__(self) -> None:
        self.reply = "你好，我是 DigitalLife 中的 AI 助手。"
        self.fail = False
        self.calls: list[list[LLMMessage]] = []

    def generate_reply(self, messages: list[LLMMessage]) -> str:
        self.calls.append(list(messages))
        if self.fail:
            raise LLMProviderError("fake provider failure")
        return self.reply


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
