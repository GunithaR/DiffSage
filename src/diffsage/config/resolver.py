import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.file_loader import load_config
from diffsage.config.paths import get_global_config_path, get_local_config_path
from diffsage.config.schema import DiffSageConfig, PartialDiffSageConfig
from diffsage.config.scope import ConfigScope
from diffsage.config.settings import Settings
from diffsage.exceptions import ConfigError, LocalConfigUnavailableError
from diffsage.models.config import ConfigSources

# Environment variable -> (config section, option)
ENVIRONMENT_VARIABLES: dict[str, tuple[str, str]] = {
    "DIFFSAGE_PROVIDER": ("ai", "provider"),
    "DIFFSAGE_AI_MODEL": ("ai", "model"),
    "DIFFSAGE_CREDENTIAL_PROFILE": ("ai", "credential_profile"),
    "DIFFSAGE_TIMEOUT": ("network", "timeout"),
    "DIFFSAGE_MAX_RETRIES": ("network", "max_retries"),
    "DIFFSAGE_LOG_LEVEL": ("logging", "level"),
}


def _environment_overrides() -> PartialDiffSageConfig:
    """Validate DIFFSAGE_* variables against the same schema as the config files."""

    data: dict[str, dict[str, str]] = {}

    for name, (section, option) in ENVIRONMENT_VARIABLES.items():
        value = os.environ.get(name)

        if value is not None:
            data.setdefault(section, {})[option] = value

    try:
        return PartialDiffSageConfig.model_validate(data)

    except ValidationError as error:
        variable_for = {location: name for name, location in ENVIRONMENT_VARIABLES.items()}
        problems = []

        for detail in error.errors():
            location = tuple(str(part) for part in detail["loc"])
            name = variable_for.get((location[0], location[-1]), ".".join(location))
            problems.append(f"{name}: {detail['msg']} (got {detail['input']!r})")

        raise ConfigError(f"Invalid environment variable {'; '.join(problems)}") from error


def _merge_dict(
    base: Mapping[str, Any],
    override: Mapping[str, Any],
) -> dict[str, Any]:
    """Recursively merge two mappings into a new dictionary."""

    merged = dict(base)

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
        credential_profile=config.ai.credential_profile,
        timeout=config.network.timeout,
        max_retries=config.network.max_retries,
        log_level=config.logging.level,
    )


def default_settings() -> Settings:
    """Return the built-in default settings, ignoring config files and environment."""

    return _to_settings(DEFAULT_CONFIG)


def resolve_settings() -> Settings:
    """Resolve application settings from all configuration sources.

    Sources, later overriding earlier: built-in defaults, the global config file, the
    repository's .diffsage.toml, then DIFFSAGE_* environment variables. `.env` files are
    deliberately not read: loading one copies every variable in it, including unrelated
    secrets, into DiffSage's environment and every git/gh subprocess it starts.
    """

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

    config = _merge_config(config, _environment_overrides())

    return _to_settings(config)


def resolve_config_path(scope: ConfigScope) -> Path:
    """Return the configuration file path for the given scope."""

    if scope is ConfigScope.GLOBAL:
        return get_global_config_path()

    local_path = get_local_config_path()

    if local_path is None:
        raise LocalConfigUnavailableError()

    return local_path


def configuration_sources() -> ConfigSources:
    """Return the configuration files and environment variables that currently apply."""

    global_path = get_global_config_path()
    local_path = get_local_config_path()

    return ConfigSources(
        global_file=global_path if global_path.exists() else None,
        local_file=local_path if local_path is not None and local_path.exists() else None,
        environment=[name for name in ENVIRONMENT_VARIABLES if name in os.environ],
    )
