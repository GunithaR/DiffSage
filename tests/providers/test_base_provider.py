from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider


class FakeProvider(BaseProvider):
    def generate(self, request: ProviderRequest) -> ProviderResponse:

        return ProviderResponse(
            content="Response",
            provider="Fake",
            model="Fake_Model",
            input_tokens=20,
            output_tokens=20,
            finish_reason="Completed",
            latency_ms=100
        )

def test_fake_provider_returns_provider_response():

    request = ProviderRequest(
        prompt="test_prompt",
        model="test_model",
        temperature=0.2,
        max_tokens=30
    )

    provider = FakeProvider()
    response = provider.generate(request)

    assert response.content == "Response"
    assert response.provider == "Fake"
    assert response.model == "Fake_Model"
    assert response.input_tokens == 20
    assert response.output_tokens == 20
    assert response.finish_reason == "Completed"
    assert response.latency_ms == 100

