from unittest.mock import patch

import httpx
import pytest
from google.genai import errors as genai_errors
from google.genai import types

from diffsage.exceptions import (
    AuthenticationError,
    ContentBlockedError,
    EmptyResponseError,
    InvalidRequestError,
    ModelNotFoundError,
    ProviderError,
    ProviderUnavailableError,
    RateLimitError,
    ResponseTruncatedError,
)
from diffsage.models.credentials import Credential
from diffsage.models.provider import ProviderRequest
from diffsage.providers.gemini_provider import GeminiProvider
from tests.helpers import create_settings


def create_request() -> ProviderRequest:
    return ProviderRequest(
        prompt="Hello",
        model="gemini-3.5-flash-lite",
        temperature=0.2,
        max_tokens=1000,
    )


def create_credential() -> Credential:
    return Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )


def gemini_reply(
    *parts: types.Part,
    finish_reason: types.FinishReason | None = types.FinishReason.STOP,
    usage: types.GenerateContentResponseUsageMetadata | None = None,
    prompt_feedback: types.GenerateContentResponsePromptFeedback | None = None,
    candidates: bool = True,
) -> types.GenerateContentResponse:
    """A reply shaped like the ones the Gemini SDK returns."""

    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=list(parts)),
                finish_reason=finish_reason,
            )
        ]
        if candidates
        else None,
        model_version="gemini-3.5-flash-lite",
        usage_metadata=usage,
        prompt_feedback=prompt_feedback,
    )


def generate_with_reply(reply: types.GenerateContentResponse):
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = reply

        return GeminiProvider(create_settings(), create_credential()).generate(create_request())


def test_gemini_provider_returns_provider_response():
    response = generate_with_reply(
        gemini_reply(
            types.Part(text="Hello from Gemini"),
            usage=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=10, candidates_token_count=20
            ),
        )
    )

    assert response.content == "Hello from Gemini"
    assert response.provider == "gemini"
    assert response.model == "gemini-3.5-flash-lite"
    assert response.input_tokens == 10
    assert response.output_tokens == 20
    assert response.finish_reason == "STOP"
    assert isinstance(response.latency_ms, int)
    assert response.latency_ms >= 0


def test_gemini_provider_raises_model_not_found_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=404,
            response_json={"status": "NOT_FOUND"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(ModelNotFoundError):
            provider.generate(create_request())


def test_gemini_provider_raises_authentication_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=401,
            response_json={"status": "UNAUTHENTICATED"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(AuthenticationError):
            provider.generate(create_request())


def test_gemini_provider_raises_rate_limit_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=429,
            response_json={"status": "RESOURCE_EXHAUSTED"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(RateLimitError):
            provider.generate(create_request())


def test_gemini_provider_raises_provider_unavailable_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=503,
            response_json={"status": "UNAVAILABLE"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(ProviderUnavailableError):
            provider.generate(create_request())


def test_gemini_provider_raises_deadline_exceeded_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=504,
            response_json={"status": "DEADLINE_EXCEEDED"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(ProviderUnavailableError):
            provider.generate(create_request())


def test_gemini_provider_raises_provider_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=500,
            response_json={"status": "SOME_UNKNOWN_STATUS"},
        )

        provider = GeminiProvider(
            create_settings(),
            create_credential(),
        )

        with pytest.raises(ProviderError):
            provider.generate(create_request())


def test_gemini_provider_passes_request_parameters_to_gemini() -> None:
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.return_value = gemini_reply(types.Part(text="Hello"))

        settings = create_settings()
        provider = GeminiProvider(
            settings,
            create_credential(),
        )

        request = ProviderRequest(
            prompt="Hello",
            model="gemini-3.5-flash-lite",
            temperature=0.7,
            max_tokens=1500,
        )

        provider.generate(request)

        call = client.models.generate_content.call_args

        assert call.kwargs["model"] == "gemini-3.5-flash-lite"
        assert call.kwargs["contents"] == "Hello"

        config = call.kwargs["config"]

        assert config.temperature == 0.7
        assert config.max_output_tokens == 1500


def test_gemini_provider_uses_credential_api_key() -> None:
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        credential = create_credential()

        GeminiProvider(
            create_settings(),
            credential,
        )

        mock_client.assert_called_once_with(
            api_key="test-api-key",
        )


def test_gemini_provider_raises_authentication_error_for_invalid_api_key() -> None:
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=400,
            response_json={
                "status": "INVALID_ARGUMENT",
                "details": [
                    {
                        "reason": "API_KEY_INVALID",
                    }
                ],
            },
        )

        provider = GeminiProvider(
            create_settings(),
            Credential(
                provider="gemini",
                name="default",
                api_key="test-api-key",
            ),
        )

        with pytest.raises(AuthenticationError, match="Please check your API Key."):
            provider.generate(create_request())


def generate_with_error(error: genai_errors.APIError) -> None:
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.side_effect = error

        GeminiProvider(create_settings(), create_credential()).generate(create_request())


def invalid_argument(message: str, *details: dict) -> genai_errors.APIError:
    """An INVALID_ARGUMENT error with the body shape the Gemini API returns."""

    return genai_errors.APIError(
        code=400,
        response_json={
            "error": {
                "code": 400,
                "message": message,
                "status": "INVALID_ARGUMENT",
                "details": list(details),
            }
        },
    )


def test_gemini_provider_reads_the_invalid_key_reason_from_the_nested_error_body() -> None:
    error = invalid_argument(
        "API key not valid. Please pass a valid API key.",
        {
            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
            "reason": "API_KEY_INVALID",
            "domain": "googleapis.com",
        },
    )

    with pytest.raises(AuthenticationError, match="Please check your API Key."):
        generate_with_error(error)


def test_gemini_provider_recognises_an_invalid_key_by_message_without_details() -> None:
    error = invalid_argument("API key not valid. Please pass a valid API key.")

    with pytest.raises(AuthenticationError):
        generate_with_error(error)


@pytest.mark.parametrize(
    "message",
    [
        "The input token count (1200000) exceeds the maximum number of tokens allowed (1048576).",
        "Unable to submit request because it has an empty text parameter.",
        "* GenerateContentRequest.generation_config.max_output_tokens: must be positive",
    ],
)
def test_gemini_provider_does_not_blame_the_api_key_for_other_invalid_arguments(
    message,
) -> None:
    """Regression: every 400 INVALID_ARGUMENT was reported as a bad API key, so a
    prompt that was too long told the user to check a key that worked."""

    error = invalid_argument(
        message,
        {"@type": "type.googleapis.com/google.rpc.BadRequest", "fieldViolations": []},
    )

    with pytest.raises(InvalidRequestError) as raised:
        generate_with_error(error)

    assert not isinstance(raised.value, AuthenticationError)
    assert raised.value.message == f"Gemini rejected the request: {message}"


def test_gemini_provider_invalid_argument_without_a_message_has_a_fallback() -> None:
    error = genai_errors.APIError(code=400, response_json={"status": "INVALID_ARGUMENT"})

    with pytest.raises(InvalidRequestError, match=r"^Gemini rejected the request as invalid\.$"):
        generate_with_error(error)


@pytest.mark.parametrize(
    "parts",
    [
        [types.Part(text="feat(api): add a partial")],
        [],  # thinking models can spend the whole limit before writing an answer
    ],
)
def test_gemini_provider_rejects_a_reply_cut_off_by_the_token_limit(parts) -> None:
    """Regression: a MAX_TOKENS reply was returned as if complete (or crashed when it
    had no text), so a half-written message reached the parser."""

    reply = gemini_reply(*parts, finish_reason=types.FinishReason.MAX_TOKENS)

    with pytest.raises(
        ResponseTruncatedError,
        match=r"^Gemini's reply was cut off at the output limit of 1000 tokens\.$",
    ):
        generate_with_reply(reply)


def test_gemini_provider_reports_a_blocked_prompt() -> None:
    """Regression: a blocked prompt has no candidates and crashed with an IndexError."""

    reply = gemini_reply(
        candidates=False,
        prompt_feedback=types.GenerateContentResponsePromptFeedback(
            block_reason=types.BlockedReason.SAFETY,
            block_reason_message="The prompt was blocked due to safety.",
        ),
    )

    with pytest.raises(ContentBlockedError) as raised:
        generate_with_reply(reply)

    assert raised.value.message == (
        "Gemini blocked the prompt (reason: SAFETY). The prompt was blocked due to safety."
    )


@pytest.mark.parametrize(
    "finish_reason", [types.FinishReason.SAFETY, types.FinishReason.RECITATION]
)
def test_gemini_provider_reports_a_reply_stopped_for_policy_reasons(finish_reason) -> None:
    reply = gemini_reply(finish_reason=finish_reason)

    with pytest.raises(
        ContentBlockedError,
        match=rf"^Gemini stopped the reply \(reason: {finish_reason.value}\)\.$",
    ):
        generate_with_reply(reply)


def test_gemini_provider_reports_a_reply_with_no_candidates() -> None:
    with pytest.raises(EmptyResponseError, match=r"^Gemini returned no reply\.$"):
        generate_with_reply(gemini_reply(candidates=False))


@pytest.mark.parametrize(
    "reply",
    [
        gemini_reply(),
        gemini_reply(types.Part(text="   \n")),
        types.GenerateContentResponse(
            candidates=[types.Candidate(content=None, finish_reason=types.FinishReason.STOP)]
        ),
    ],
    ids=["no-parts", "whitespace", "no-content"],
)
def test_gemini_provider_reports_an_empty_reply(reply) -> None:
    """Regression: a reply without text crashed (IndexError / AttributeError) or was
    passed on as an empty string."""

    with pytest.raises(
        EmptyResponseError, match=r"^Gemini returned an empty reply \(finish reason: STOP\)\.$"
    ):
        generate_with_reply(reply)


def test_gemini_provider_joins_text_parts_and_skips_thoughts() -> None:
    reply = gemini_reply(
        types.Part(text="Let me look at the diff first.", thought=True),
        types.Part(text="feat(api): add retries"),
        types.Part(text="\n\nRetry failed requests."),
    )

    response = generate_with_reply(reply)

    assert response.content == "feat(api): add retries\n\nRetry failed requests."


def test_gemini_provider_tolerates_missing_usage_model_and_finish_reason() -> None:
    """Regression: a reply without usage metadata crashed with an AttributeError."""

    reply = types.GenerateContentResponse(
        candidates=[
            types.Candidate(content=types.Content(role="model", parts=[types.Part(text="ok")]))
        ]
    )

    response = generate_with_reply(reply)

    assert response.content == "ok"
    assert response.model == create_request().model
    assert response.input_tokens is None
    assert response.output_tokens is None
    assert response.finish_reason is None


def rate_limited(*details: dict, headers: dict[str, str] | None = None) -> genai_errors.APIError:
    """A 429 shaped like the Gemini API's, optionally with an HTTP response's headers."""

    return genai_errors.APIError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "You exceeded your current quota.",
                "status": "RESOURCE_EXHAUSTED",
                "details": list(details),
            }
        },
        response=httpx.Response(429, headers=headers) if headers is not None else None,
    )


@pytest.mark.parametrize(
    ("error", "retry_after", "message"),
    [
        (
            rate_limited(
                {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": []},
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "37s"},
            ),
            37.0,
            "Gemini API rate limit exceeded. Gemini asked to wait 37 seconds before trying again.",
        ),
        (
            rate_limited(
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "0.5s"}
            ),
            0.5,
            "Gemini API rate limit exceeded. Gemini asked to wait 1 seconds before trying again.",
        ),
        (
            rate_limited(headers={"Retry-After": "12"}),
            12.0,
            "Gemini API rate limit exceeded. Gemini asked to wait 12 seconds before trying again.",
        ),
        (
            rate_limited(
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3600s"}
            ),
            3600.0,
            "Gemini API rate limit exceeded. Gemini asked to wait 60 minutes before trying again.",
        ),
        (
            rate_limited(headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}),
            None,
            "Gemini API rate limit exceeded.",
        ),
        (rate_limited(), None, "Gemini API rate limit exceeded."),
    ],
    ids=["retry-info", "fractional", "retry-after-header", "long-wait", "http-date", "no-hint"],
)
def test_gemini_provider_passes_on_the_suggested_wait_of_a_rate_limit(
    error, retry_after, message
) -> None:
    with pytest.raises(RateLimitError) as raised:
        generate_with_error(error)

    assert raised.value.retry_after == retry_after
    assert raised.value.message == message
