from diffsage.config.resolver import default_settings, resolve_settings
from diffsage.config.settings import Settings
from diffsage.exceptions import ConfigError

__all__ = ["default_settings", "load_settings", "load_settings_or_defaults"]


def load_settings() -> Settings:
    """Load application settings."""

    return resolve_settings()


def load_settings_or_defaults() -> Settings:
    """Load settings, falling back to the built-in defaults if the configuration is invalid.

    For commands that must keep working with a broken configuration so it can be
    inspected or repaired.
    """

    try:
        return resolve_settings()
    except ConfigError:
        return default_settings()
