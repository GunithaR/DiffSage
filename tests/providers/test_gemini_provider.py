import pytest

from unittest.mock import Mock, patch
from google.genai import errors as genai_errors

from diffsage.config.settings import Settings
from diffsage.models.provider import ProviderRequest
from diffsage.providers.gemini_provider import GeminiProvider
from diffsage.exceptions import (
    ModelNotFoundError,
    AuthenticationError,
    RateLimitError,
    ProviderUnavailableError,
    ProviderError,
)
from tests.helpers import create_settings


def create_request() -> ProviderRequest:
    return ProviderRequest(
        prompt="Hello",
        model="gemini-3.5-flash-lite",
        temperature=0.2,
        max_tokens=1000,
    )


def test_gemini_provider_returns_provider_response():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value
        mock_response = Mock()

        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content.parts = [Mock()]
        mock_response.candidates[0].content.parts[0].text = "Hello from Gemini"

        mock_response.candidates[0].finish_reason.value = "STOP"

        mock_response.model_version = "gemini-3.5-flash-lite"

        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20

        client.models.generate_content.return_value = mock_response

        provider = GeminiProvider(create_settings())

        response = provider.generate(create_request())

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

        provider = GeminiProvider(create_settings())

        with pytest.raises(ModelNotFoundError):
            provider.generate(create_request())


def test_gemini_provider_raises_authentication_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=401,
            response_json={"status": "UNAUTHENTICATED"},
        )

        provider = GeminiProvider(create_settings())

        with pytest.raises(AuthenticationError):
            provider.generate(create_request())


def test_gemini_provider_raises_rate_limit_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=429,
            response_json={"status": "RESOURCE_EXHAUSTED"},
        )

        provider = GeminiProvider(create_settings())

        with pytest.raises(RateLimitError):
            provider.generate(create_request())


def test_gemini_provider_raises_provider_unavailable_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=503,
            response_json={"status": "UNAVAILABLE"},
        )

        provider = GeminiProvider(create_settings())

        with pytest.raises(ProviderUnavailableError):
            provider.generate(create_request())


def test_gemini_provider_raises_deadline_exceeded_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=504,
            response_json={"status": "DEADLINE_EXCEEDED"},
        )

        provider = GeminiProvider(create_settings())

        with pytest.raises(ProviderUnavailableError):
            provider.generate(create_request())


def test_gemini_provider_raises_provider_error():
    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value

        client.models.generate_content.side_effect = genai_errors.APIError(
            code=500,
            response_json={"status": "SOME_UNKNOWN_STATUS"},
        )

        provider = GeminiProvider(create_settings())

        with pytest.raises(ProviderError):
            provider.generate(create_request())
