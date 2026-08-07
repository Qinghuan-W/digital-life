from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "DigitalLife API"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    test_database_url: str
    jwt_secret: str = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=365)
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str | None = None
    llm_api_mode: Literal["responses", "chat_completions"] = "responses"
    llm_json_mode_enabled: bool = True
    llm_structured_output_enabled: bool = True
    llm_timeout_seconds: float = Field(default=30, ge=1, le=120)
    llm_history_limit: int = Field(default=20, ge=1, le=50)
    cors_origins: list[str] = [
        "http://127.0.0.1:8081",
        "http://localhost:8081",
    ]

    @property
    def active_database_url(self) -> str:
        return self.test_database_url if self.app_env == "test" else self.database_url

    @property
    def normalized_openai_base_url(self) -> str | None:
        value = self.openai_base_url.strip() if self.openai_base_url else ""
        return value or None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
