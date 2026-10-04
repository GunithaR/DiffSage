import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import load_dotenv

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.file_loader import load_config
from diffsage.config.paths import get_global_config_path, get_local_config_path
from diffsage.config.schema import DiffSageConfig, PartialDiffSageConfig
from diffsage.config.scope import ConfigScope
from diffsage.config.settings import Settings
from diffsage.exceptions import ConfigError


def _merge_dict(
    base: dict,
    override: dict,
) -> dict:
    """Recursively merge two dictionaries."""

    merged = base.copy()

    for key, value in override.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value

    return merged


def _merge_config(
    base: DiffSageConfig,
    override: PartialDiffSageConfig,
) -> DiffSageConfig:
    """Merge two configuration models."""

    merged = _merge_dict(
        base.model_dump(),
        override.model_dump(exclude_unset=True),
    )

    return DiffSageConfig.model_validate(merged)


def _to_settings(config: DiffSageConfig) -> Settings:
    """Convert a configuration model into runtime settings."""

    return Settings(
        provider=config.ai.provider,
        ai_model=config.ai.model,
        timeout=config.network.timeout,
        max_retries=config.network.max_retries,
        log_level=config.logging.level,
    )


def default_settings() -> Settings:
    """Return the built-in default settings, ignoring config files and environment."""

    return _to_settings(DEFAULT_CONFIG)


def resolve_settings() -> Settings:
    """Resolve application settings from all configuration sources."""

    load_dotenv()

    config = DEFAULT_CONFIG
    global_config_path = get_global_config_path()

    if global_config_path.exists():
        config = _merge_config(
            config,
            load_config(global_config_path),
        )

    local_config_path = get_local_config_path()

    if local_config_path is not None and local_config_path.exists():
        config = _merge_config(config, load_config(local_config_path))

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


def resolve_config_path(scope: ConfigScope) -> Path:
    """Return the configuration path for the given scope"""

    if scope is ConfigScope.GLOBAL:
        return get_global_config_path()

    return get_local_config_path()
