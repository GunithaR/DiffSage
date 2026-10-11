"""Create AI providers by name: the one place that knows which providers exist."""

from collections.abc import Callable

from diffsage.config.settings import Settings
from diffsage.exceptions.base import ConfigError
from diffsage.models.credentials import Credential
from diffsage.providers.base import BaseProvider

ProviderFactory = Callable[[Settings, Credential], BaseProvider]


def _gemini(settings: Settings, credential: Credential) -> BaseProvider:
    # Imported on first use: the Gemini SDK takes about a third of a second to import,
    # which every command would otherwise pay, including ones that never call the AI.
    from diffsage.providers.gemini_provider import GeminiProvider

    return GeminiProvider(settings, credential)


# Provider name (the `provider` setting) -> factory. Adding a provider means adding a
# module in this package and an entry here; the configuration schema reads the
# supported names from this registry, so nothing outside providers/ changes.
PROVIDERS: dict[str, ProviderFactory] = {
    "gemini": _gemini,
}


def create_provider(settings: Settings, credential: Credential) -> BaseProvider:
    """Create the configured AI provider."""

    factory = PROVIDERS.get(settings.provider)

    if factory is None:
        raise ConfigError(f"Unsupported provider: {settings.provider}")

    return factory(settings, credential)
