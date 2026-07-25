from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider
from diffsage.providers.gemini_provider import GeminiProvider


class GeminiProvider(BaseProvider):

    def generate(self, request) -> ProviderResponse:

        return ProviderResponse(
            content="GeminiResponse",
            provider="Gemini",
            model="Gemini 3.6 Flash",
            input_tokens=100,
            output_tokens=100,
            finish_reason="Completed",
            latency_ms=100
        )

def test_gemini_provider_returns_provider_response():

    request = ProviderRequest(
            prompt="test_prompt",
            model="gemini_model",
            temperature=0.2,
            max_tokens=30
    )

    provider = GeminiProvider()
    response = provider.generate(request)

    assert response.content == "GeminiResponse"
    assert response.provider == "Gemini"
    assert response.model == "Gemini 3.6 Flash"
    assert response.input_tokens == 100
    assert response.output_tokens == 100
    assert response.finish_reason == "Completed"
    assert response.latency_ms == 100