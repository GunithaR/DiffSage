from diffsage.config.settings import Settings
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.factory import create_provider

class AIService:
    """Coordinates AI provider interactions."""

    def __init__(self, settings: Settings) -> None:
        self._provider = create_provider(settings)

    def ask(self, prompt: str) -> ProviderResponse:

        request = ProviderRequest(
            prompt=prompt,
            model="gemini-3.5-flash-lite", # TODO: Move model configuration into Settings.
            temperature=0.2,
            max_tokens=1000,
        )

        return self._provider.generate(request)