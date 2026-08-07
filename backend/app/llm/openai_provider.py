import json
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.llm.prompt_builder import build_model_input
from app.llm.provider import GeneratedAssistantTurn, LLMMessage, LLMProviderError


logger = logging.getLogger("digitallife.llm")
ParseMode = Literal["structured", "json_object", "json_array", "plain_text_fallback"]
_SAFE_METADATA = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
ASSISTANT_TURN_JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "messages": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 4,
        },
        "conversation_signal": {
            "type": "string",
            "enum": [
                "urgent",
                "distressed",
                "affectionate",
                "playful",
                "neutral",
                "complex",
            ],
        },
    },
    "required": ["messages", "conversation_signal"],
    "additionalProperties": False,
}


class OpenAIProvider:
    """OpenAI-compatible provider with an explicitly configured API surface."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        api_key = (self.settings.openai_api_key or "").strip()
        if not api_key:
            raise LLMProviderError(
                "The model provider is not configured",
                provider_operation="client.create",
                api_mode=self.settings.llm_api_mode,
                model=self._model_name(),
                provider_error_type="configuration_error",
            )
        if self._client is None:
            common = {
                "api_key": api_key,
                "timeout": self.settings.llm_timeout_seconds,
                "max_retries": 0,
            }
            base_url = self.settings.normalized_openai_base_url
            self._client = OpenAI(base_url=base_url, **common) if base_url else OpenAI(**common)
        return self._client

    def _model_name(self) -> str | None:
        model = (self.settings.openai_model or "").strip()
        return model or None

    def generate_reply(
        self,
        *,
        system_prompt: str,
        identity_reminder: str,
        messages: Sequence[LLMMessage],
    ) -> GeneratedAssistantTurn:
        model = self._model_name()
        if model is None:
            raise LLMProviderError(
                "The model provider is not configured",
                provider_operation="request.prepare",
                api_mode=self.settings.llm_api_mode,
                provider_error_type="configuration_error",
            )

        if self.settings.llm_api_mode == "responses":
            raw_output = self._generate_with_responses(
                model=model,
                system_prompt=system_prompt,
                identity_reminder=identity_reminder,
                messages=messages,
            )
        else:
            raw_output = self._generate_with_chat_completions(
                model=model,
                system_prompt=system_prompt,
                identity_reminder=identity_reminder,
                messages=messages,
            )

        turn, parse_mode = _parse_generated_assistant_turn_with_mode(raw_output)
        logger.info(
            "LLM response parsed: api_mode=%s parse_mode=%s message_count=%s",
            self.settings.llm_api_mode,
            parse_mode,
            len(turn.messages),
        )
        return turn

    def _generate_with_responses(
        self,
        *,
        model: str,
        system_prompt: str,
        identity_reminder: str,
        messages: Sequence[LLMMessage],
    ) -> object:
        model_input = build_model_input(messages)
        # Reassert current identity after legacy history without persisting the reminder.
        model_input.append({"role": "developer", "content": identity_reminder})
        request: dict[str, Any] = {
            "model": model,
            "instructions": system_prompt,
            "input": model_input,
            "store": False,
            "stream": False,
        }
        if self.settings.llm_structured_output_enabled:
            request["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "generated_assistant_turn",
                    "schema": ASSISTANT_TURN_JSON_SCHEMA,
                    "strict": True,
                }
            }
        try:
            response = self._get_client().responses.create(**request)
        except OpenAIError as exc:
            raise self._normalize_provider_error(exc, "responses.create", model) from exc

        parsed = getattr(response, "output_parsed", None)
        if isinstance(parsed, (Mapping, BaseModel)):
            return parsed
        return getattr(response, "output_text", "")

    def _generate_with_chat_completions(
        self,
        *,
        model: str,
        system_prompt: str,
        identity_reminder: str,
        messages: Sequence[LLMMessage],
    ) -> object:
        chat_messages = [{"role": "system", "content": system_prompt}]
        chat_messages.extend(build_model_input(messages))
        # Compatible providers may reject the developer role, so use a final system rule.
        chat_messages.append({"role": "system", "content": identity_reminder})
        request: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "stream": False,
        }
        if self.settings.llm_json_mode_enabled:
            request["response_format"] = {"type": "json_object"}
        try:
            response = self._get_client().chat.completions.create(**request)
        except OpenAIError as exc:
            raise self._normalize_provider_error(exc, "chat.completions.create", model) from exc

        message = response.choices[0].message
        parsed = getattr(message, "parsed", None)
        if isinstance(parsed, (Mapping, BaseModel)):
            return parsed
        return message.content or ""

    def _normalize_provider_error(
        self,
        exc: OpenAIError,
        provider_operation: str,
        model: str,
    ) -> LLMProviderError:
        status_code = getattr(exc, "status_code", None)
        error_type = _safe_error_metadata(type(exc).__name__)
        error_code = None
        body = getattr(exc, "body", None)
        if isinstance(body, Mapping):
            error_data = body.get("error", body)
            if isinstance(error_data, Mapping):
                error_type = _safe_error_metadata(error_data.get("type")) or error_type
                error_code = _safe_error_metadata(error_data.get("code"))
        retryable = bool(
            status_code in {408, 409, 429}
            or (isinstance(status_code, int) and status_code >= 500)
            or type(exc).__name__ in {"APIConnectionError", "APITimeoutError"}
        )
        logger.warning(
            "LLM request failed: provider_operation=%s api_mode=%s model=%s "
            "status=%s error_type=%s error_code=%s retryable=%s",
            provider_operation,
            self.settings.llm_api_mode,
            model,
            status_code,
            error_type,
            error_code,
            retryable,
        )
        return LLMProviderError(
            provider_operation=provider_operation,
            api_mode=self.settings.llm_api_mode,
            model=model,
            http_status=status_code if isinstance(status_code, int) else None,
            provider_error_type=error_type,
            provider_error_code=error_code,
            retryable=retryable,
        )


def parse_generated_assistant_turn(raw_output: object) -> GeneratedAssistantTurn:
    turn, _parse_mode = _parse_generated_assistant_turn_with_mode(raw_output)
    return turn


def _parse_generated_assistant_turn_with_mode(
    raw_output: object,
) -> tuple[GeneratedAssistantTurn, ParseMode]:
    if isinstance(raw_output, BaseModel):
        return _validate_generated_turn(raw_output.model_dump()), "structured"
    if isinstance(raw_output, Mapping):
        return _validate_generated_turn(dict(raw_output)), "structured"
    if not isinstance(raw_output, str):
        raise LLMProviderError("The model provider returned unsupported content")

    raw_content = raw_output.strip()
    if not raw_content:
        raise LLMProviderError("The model provider returned empty content")
    candidate = _strip_outer_code_fence(raw_content)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return _single_message_fallback(candidate), "plain_text_fallback"

    if isinstance(payload, dict):
        return _validate_generated_turn(payload), "json_object"
    if isinstance(payload, list):
        return _validate_generated_turn(
            {"messages": payload, "conversation_signal": "neutral"}
        ), "json_array"
    raise LLMProviderError("The model provider returned an invalid assistant turn")


def _validate_generated_turn(payload: object) -> GeneratedAssistantTurn:
    try:
        return GeneratedAssistantTurn.model_validate(payload)
    except ValidationError as exc:
        raise LLMProviderError("The model provider returned an invalid assistant turn") from exc


def _single_message_fallback(content: str) -> GeneratedAssistantTurn:
    return _validate_generated_turn(
        {"messages": [content], "conversation_signal": "neutral"}
    )


def _strip_outer_code_fence(content: str) -> str:
    lines = content.splitlines()
    if len(lines) >= 2 and lines[0].strip().lower() in {"```", "```json"}:
        if lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return content


def _safe_error_metadata(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if _SAFE_METADATA.fullmatch(normalized) else None
