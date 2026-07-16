from dotenv import load_dotenv
import os

from diffsage.config.settings import Settings
from diffsage.core.exceptions import ConfigError


def load_settings() -> Settings:
    """Load application settings."""

    load_dotenv()

    defaults = Settings()

    try :
        return Settings(
           provider=os.getenv("DIFFSAGE_PROVIDER", defaults.provider),
            timeout=int(os.getenv("DIFFSAGE_TIMEOUT", defaults.timeout)),
            max_retries=int(os.getenv("DIFFSAGE_MAX_RETRIES", defaults.max_retries)),
            log_level=os.getenv("DIFFSAGE_LOG_LEVEL", defaults.log_level)
        )
    except ValueError as error:
        raise ConfigError("Invalid configuration value.") from error