import time

from google import genai
from google.genai import errors as genai_errors

from diffsage.providers.base import BaseProvider
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.config.settings import Settings
from diffsage.exceptions import ModelNotFoundError, ProviderError

class GeminiProvider(BaseProvider):

    def __init__(self, settings: Settings) -> None:
        self._settings=settings

        self._client = genai.Client(
            api_key=self._settings.api_key
        )

    def generate(self, request: ProviderRequest) -> ProviderResponse:

        start_time = time.perf_counter()

        try:
            response = self._client.models.generate_content(
                model=request.model,
                contents=request.prompt,
            )
        except genai_errors.APIError as e:
            if e.status == "NOT_FOUND":
                raise ModelNotFoundError(
                    f"Model '{request.model}' was not found."
                ) from e

            raise ProviderError(
                f"Gemini API request failed: {e}"
            ) from e

        latency_ms = round((time.perf_counter() - start_time) * 1000)

        return ProviderResponse(
            content=response.candidates[0].content.parts[0].text,
            provider="gemini",
            model=response.model_version,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            finish_reason=response.candidates[0].finish_reason.value,
            latency_ms=latency_ms
        )