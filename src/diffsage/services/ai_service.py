from diffsage.config.loader import load_settings
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.factory import create_provider

class AIService:
    """Coordinates AI provider interactions."""

    def ask(self, prompt: str) -> ProviderResponse:

        settings = load_settings()
        provider = create_provider(settings)

        request = ProviderRequest(
            prompt=prompt,
            model="gemini-3.5-flash-lite", # TODO: Move model configuration into Settings.
            temperature=0.2,
            max_tokens=1000,
        )

        return provider.generate(request)