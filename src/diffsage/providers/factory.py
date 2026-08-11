from diffsage.config.settings import Settings
from diffsage.exceptions.base import ConfigError
from diffsage.models.credentials import Credential
from diffsage.providers.base import BaseProvider
from diffsage.providers.gemini_provider import GeminiProvider


def create_provider(settings: Settings, credential: Credential) -> BaseProvider:
    """Create the configured AI provider."""

    if settings.provider == "gemini":
        return GeminiProvider(settings, credential)

    raise ConfigError(f"Unsupported provider: {settings.provider}")
