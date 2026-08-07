import logging
from unittest.mock import Mock

import httpx
import pytest
from openai import APIStatusError, APITimeoutError
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.openai_provider import OpenAIProvider, parse_generated_assistant_turn
from app.llm.provider import GeneratedAssistantTurn, LLMMessage, LLMProviderError


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "database_url": "postgresql+psycopg://test:test@localhost/test",
        "test_database_url": "postgresql+psycopg://test:test@localhost/test_test",
        "jwt_secret": "x" * 32,
        "openai_api_key": "test-key",
        "openai_model": "test-model",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def provider_with_mock_client(**settings: object) -> tuple[OpenAIProvider, Mock]:
    provider = OpenAIProvider(make_settings(**settings))
    client = Mock()
    provider._client = client
    return provider, client


def generate(provider: OpenAIProvider) -> GeneratedAssistantTurn:
    return provider.generate_reply(
        system_prompt="SYSTEM_SENTINEL",
        identity_reminder="IDENTITY_SENTINEL",
        messages=[
            LLMMessage(role="assistant", content="OLD_ASSISTANT_SENTINEL"),
            LLMMessage(role="user", content="CURRENT_USER_SENTINEL"),
        ],
    )


def test_responses_mode_uses_only_responses_adapter_with_structured_output() -> None:
    provider, client = provider_with_mock_client(llm_api_mode="responses")
    client.responses.create.return_value.output_text = (
        '{"messages":["a","b"],"conversation_signal":"playful"}'
    )
    turn = generate(provider)
    assert turn == GeneratedAssistantTurn(messages=["a", "b"], conversation_signal="playful")
    client.responses.create.assert_called_once()
    client.chat.completions.create.assert_not_called()
    request = client.responses.create.call_args.kwargs
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True
    assert request["store"] is False
    assert request["stream"] is False


def test_responses_mode_omits_structured_output_when_disabled() -> None:
    provider, client = provider_with_mock_client(
        llm_api_mode="responses",
        llm_structured_output_enabled=False,
    )
    client.responses.create.return_value.output_text = '{"messages":["a"]}'
    generate(provider)
    assert "text" not in client.responses.create.call_args.kwargs


def test_chat_completions_mode_converts_roles_without_duplicate_user_message() -> None:
    provider, client = provider_with_mock_client(llm_api_mode="chat_completions")
    client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content='{"messages":["a","b"],"conversation_signal":"neutral"}'))
    ]
    turn = generate(provider)
    assert turn.messages == ["a", "b"]
    client.chat.completions.create.assert_called_once()
    client.responses.create.assert_not_called()
    request = client.chat.completions.create.call_args.kwargs
    assert request["response_format"] == {"type": "json_object"}
    assert request["stream"] is False
    assert request["messages"] == [
        {"role": "system", "content": "SYSTEM_SENTINEL"},
        {"role": "assistant", "content": "OLD_ASSISTANT_SENTINEL"},
        {"role": "user", "content": "CURRENT_USER_SENTINEL"},
        {"role": "system", "content": "IDENTITY_SENTINEL"},
    ]
    assert sum(
        item["content"] == "CURRENT_USER_SENTINEL" for item in request["messages"]
    ) == 1


def test_chat_completions_omits_json_mode_when_disabled() -> None:
    provider, client = provider_with_mock_client(
        llm_api_mode="chat_completions",
        llm_json_mode_enabled=False,
    )
    client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content='{"messages":["a"]}'))
    ]
    generate(provider)
    assert "response_format" not in client.chat.completions.create.call_args.kwargs


def test_both_api_modes_return_the_same_generated_turn() -> None:
    expected = GeneratedAssistantTurn(
        messages=["first", "second"],
        conversation_signal="affectionate",
    )
    responses_provider, responses_client = provider_with_mock_client(llm_api_mode="responses")
    responses_client.responses.create.return_value.output_text = expected.model_dump_json()
    chat_provider, chat_client = provider_with_mock_client(llm_api_mode="chat_completions")
    chat_client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content=expected.model_dump_json()))
    ]
    assert generate(responses_provider) == expected
    assert generate(chat_provider) == expected


def make_status_error(status_code: int) -> APIStatusError:
    request = httpx.Request("POST", "https://provider.invalid/v1")
    response = httpx.Response(status_code, request=request)
    return APIStatusError(
        "RAW_SECRET_ERROR_MESSAGE",
        response=response,
        body={"error": {"type": "provider_error", "code": "safe_code"}},
    )


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_provider_errors_never_switch_api_mode_or_retry(status_code: int) -> None:
    provider, client = provider_with_mock_client(llm_api_mode="chat_completions")
    client.chat.completions.create.side_effect = make_status_error(status_code)
    with pytest.raises(LLMProviderError) as captured:
        generate(provider)
    assert captured.value.http_status == status_code
    assert captured.value.api_mode == "chat_completions"
    client.chat.completions.create.assert_called_once()
    client.responses.create.assert_not_called()


def test_timeout_never_switches_api_mode_or_retries() -> None:
    provider, client = provider_with_mock_client(llm_api_mode="responses")
    client.responses.create.side_effect = APITimeoutError(
        request=httpx.Request("POST", "https://provider.invalid/v1")
    )
    with pytest.raises(LLMProviderError) as captured:
        generate(provider)
    assert captured.value.api_mode == "responses"
    assert captured.value.retryable is True
    client.responses.create.assert_called_once()
    client.chat.completions.create.assert_not_called()


def test_safe_error_log_contains_metadata_but_not_request_content_or_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    provider, client = provider_with_mock_client(llm_api_mode="chat_completions")
    client.chat.completions.create.side_effect = make_status_error(404)
    with caplog.at_level(logging.WARNING, logger="digitallife.llm"):
        with pytest.raises(LLMProviderError):
            generate(provider)
    output = caplog.text
    assert "api_mode=chat_completions" in output
    assert "status=404" in output
    assert "error_code=safe_code" in output
    for secret in [
        "RAW_SECRET_ERROR_MESSAGE",
        "SYSTEM_SENTINEL",
        "IDENTITY_SENTINEL",
        "CURRENT_USER_SENTINEL",
        "test-key",
        "Bearer",
        "password",
    ]:
        assert secret not in output
    assert "conversation_signal" not in output


def test_invalid_llm_api_mode_is_rejected_by_settings() -> None:
    with pytest.raises(ValidationError):
        make_settings(llm_api_mode="auto")


@pytest.mark.parametrize(
    ("raw_output", "messages", "signal"),
    [
        ('{"messages":["a","b"],"conversation_signal":"playful"}', ["a", "b"], "playful"),
        ('{"messages":["1","2","3","4"],"conversation_signal":"complex"}', ["1", "2", "3", "4"], "complex"),
        ('```json\n{"messages":["a"],"conversation_signal":"neutral"}\n```', ["a"], "neutral"),
        ('["a","b"]', ["a", "b"], "neutral"),
        ("plain.\ntext, remains whole", ["plain.\ntext, remains whole"], "neutral"),
    ],
)
def test_parser_supported_shapes(
    raw_output: object,
    messages: list[str],
    signal: str,
) -> None:
    turn = parse_generated_assistant_turn(raw_output)
    assert turn.messages == messages
    assert turn.conversation_signal == signal


def test_parser_accepts_sdk_parsed_object_and_filters_blank_items() -> None:
    turn = parse_generated_assistant_turn(
        {"messages": [" a ", " ", "b"], "conversation_signal": "invalid"}
    )
    assert turn.messages == ["a", "b"]
    assert turn.conversation_signal == "neutral"


@pytest.mark.parametrize(
    "raw_output",
    [
        '{"messages":[]}',
        '{"messages":[" "]}',
        '{"messages":["1","2","3","4","5"]}',
        '{"messages":["a", 2]}',
        '{"messages":[{"content":"a"}]}',
        '{"other":"a"}',
    ],
)
def test_parser_rejects_invalid_structured_output(raw_output: str) -> None:
    with pytest.raises(LLMProviderError):
        parse_generated_assistant_turn(raw_output)


def test_invalid_format_does_not_make_a_second_provider_call() -> None:
    provider, client = provider_with_mock_client(llm_api_mode="chat_completions")
    client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content='{"messages":[]}'))
    ]
    with pytest.raises(LLMProviderError):
        generate(provider)
    client.chat.completions.create.assert_called_once()
    client.responses.create.assert_not_called()
