from diffsage.config.settings import Settings

from diffsage.providers.base import BaseProvider
from diffsage.providers.gemini_provider import GeminiProvider

def create_provider(settings: Settings) -> BaseProvider:
    """Create the configured AI provider."""
    return GeminiProvider(settings)