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
from app.main import app  # noqa: E402


if not str(engine.url).endswith("/digitallife_test"):
    raise RuntimeError("Tests must use the digitallife_test database.")


@pytest.fixture(autouse=True)
def clean_test_database() -> Generator[None, None, None]:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE refresh_tokens, users CASCADE"))
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
