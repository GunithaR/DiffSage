import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from diffsage.config.settings import Settings
from diffsage.exceptions import (
    AuthenticationError,
    ModelNotFoundError,
    ProviderError,
    ProviderUnavailableError,
    RateLimitError,
)
from diffsage.models.credentials import Credential
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini provider implementation."""

    def __init__(self, settings: Settings, credential: Credential) -> None:
        self._settings = settings
        self._credential = credential

        self._client = genai.Client(api_key=self._credential.api_key)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        start_time = time.perf_counter()

        timeout_ms = self._settings.timeout * 1000

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

        try:
            response = self._client.models.generate_content(
                model=request.model, contents=request.prompt, config=config
            )
        except genai_errors.APIError as e:
            status = e.status

            if status == "NOT_FOUND":
                raise ModelNotFoundError(f"Model '{request.model}' was not found.") from e

            elif status == "UNAUTHENTICATED":
                raise AuthenticationError("Authentication with Gemini failed.") from e

            elif status == "INVALID_ARGUMENT":
                if e.code == 400:
                    raise AuthenticationError(
                        "Authentication with Gemini failed. Please check your API Key."
                    ) from e

            elif status == "RESOURCE_EXHAUSTED":
                raise RateLimitError("Gemini API rate limit exceeded.") from e

            elif status in ("UNAVAILABLE", "DEADLINE_EXCEEDED"):
                raise ProviderUnavailableError("Gemini service is currently unavailable.") from e

            raise ProviderError(f"Gemini API request failed: {e}") from e

        latency_ms = round((time.perf_counter() - start_time) * 1000)

        return ProviderResponse(
            content=response.candidates[0].content.parts[0].text,
            provider="gemini",
            model=response.model_version,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            finish_reason=response.candidates[0].finish_reason.value,
            latency_ms=latency_ms,
        )
