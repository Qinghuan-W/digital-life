from collections.abc import Sequence

from openai import OpenAI, OpenAIError

from app.core.config import Settings, get_settings
from app.llm.prompt_builder import SYSTEM_PROMPT, build_model_input
from app.llm.provider import LLMMessage, LLMProviderError


class OpenAIProvider:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        api_key = (self.settings.openai_api_key or "").strip()
        if not api_key:
            raise LLMProviderError("OpenAI API key is not configured")
        if self._client is None:
            common = {
                "api_key": api_key,
                "timeout": self.settings.llm_timeout_seconds,
                "max_retries": 0,
            }
            base_url = self.settings.normalized_openai_base_url
            self._client = OpenAI(base_url=base_url, **common) if base_url else OpenAI(**common)
        return self._client

    def generate_reply(self, messages: Sequence[LLMMessage]) -> str:
        model = (self.settings.openai_model or "").strip()
        if not model:
            raise LLMProviderError("OpenAI model is not configured")
        try:
            response = self._get_client().responses.create(
                model=model,
                instructions=SYSTEM_PROMPT,
                input=build_model_input(messages),
                store=False,
            )
        except OpenAIError as exc:
            raise LLMProviderError("The model provider request failed") from exc

        content = response.output_text.strip()
        if not content:
            raise LLMProviderError("The model provider returned empty content")
        return content
