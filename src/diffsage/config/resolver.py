import os

from dotenv import load_dotenv

from diffsage.config.settings import Settings
from diffsage.config.schema import DiffSageConfig
from diffsage.exceptions.base import ConfigError


def _merge_config(
        base: DiffSageConfig,
        override: DiffSageConfig,
) -> DiffSageConfig:
    ...

def _to_settings(config: DiffSageConfig) -> Settings:
    ...    

def resolve_settings() -> Settings:
    """Resolve application settings from all configuration sources."""

    load_dotenv()

    defaults = Settings()

    try:
        #
        # Resolution order (current)
        #
        # Defaults
        #     ↓
        # Environment Variables
        #

        return Settings(
            provider=os.getenv(
                "DIFFSAGE_PROVIDER",
                defaults.provider,
            ),
            ai_model=os.getenv(
                "DIFFSAGE_AI_MODEL",
                defaults.ai_model,
            ),
            api_key=os.getenv(
                "DIFFSAGE_API_KEY",
                defaults.api_key,
            ),
            timeout=int(
                os.getenv(
                    "DIFFSAGE_TIMEOUT",
                    str(defaults.timeout),
                )
            ),
            max_retries=int(
                os.getenv(
                    "DIFFSAGE_MAX_RETRIES",
                    str(defaults.max_retries),
                )
            ),
            log_level=os.getenv(
                "DIFFSAGE_LOG_LEVEL",
                defaults.log_level,
            ),
        )

    except ValueError as error:
        raise ConfigError("Invalid configuration value.") from error