from diffsage.config.settings import Settings
from diffsage.providers.base import BaseProvider
from diffsage.providers.gemini_provider import GeminiProvider
from diffsage.exceptions.base import ConfigError


def create_provider(settings: Settings) -> BaseProvider:
    """Create the configured AI provider."""

    if settings.provider == "gemini":
        return GeminiProvider(settings)

    raise ConfigError(
        f"Unsupported provider: {settings.provider}"
    )
