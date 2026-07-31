from diffsage.config.resolver import resolve_settings
from diffsage.config.settings import Settings


def load_settings() -> Settings:
    """Load application settings."""

    return resolve_settings()