import os

from dotenv import load_dotenv

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.settings import Settings
from diffsage.config.schema import DiffSageConfig
from diffsage.exceptions.base import ConfigError

from diffsage.config.paths import get_global_config_path
from diffsage.config.file_loader import load_config


def _merge_config(
        base: DiffSageConfig,
        override: DiffSageConfig,
) -> DiffSageConfig:
    ...


def _to_settings(config: DiffSageConfig) -> Settings:
    """Convert a configuration model into runtime settings."""

    return Settings(
        provider=config.ai.provider,
        ai_model=config.ai.model,
        api_key=os.getenv("DIFFSAGE_API_KEY", ""),
        timeout=config.network.timeout,
        max_retries=config.network.max_retries,
        log_level=config.logging.level,
    )
    

def resolve_settings() -> Settings:
    """Resolve application settings from all configuration sources."""

    load_dotenv()

    config = DEFAULT_CONFIG
    global_config_path = get_global_config_path()

    if global_config_path.exists():
        global_config = load_config(global_config_path)
        config = global_config

    settings = _to_settings(config)

    try:
        return Settings(
            provider=os.getenv(
                "DIFFSAGE_PROVIDER",
                settings.provider,
            ),
            ai_model=os.getenv(
                "DIFFSAGE_AI_MODEL",
                settings.ai_model,
            ),
            api_key=os.getenv(
                "DIFFSAGE_API_KEY",
                settings.api_key,
            ),
            timeout=int(
                os.getenv(
                    "DIFFSAGE_TIMEOUT",
                    str(settings.timeout),
                )
            ),
            max_retries=int(
                os.getenv(
                    "DIFFSAGE_MAX_RETRIES",
                    str(settings.max_retries),
                )
            ),
            log_level=os.getenv(
                "DIFFSAGE_LOG_LEVEL",
                settings.log_level,
            ),
        )

    except ValueError as error:
        raise ConfigError("Invalid configuration value.") from error