from pathlib import Path
import tomllib

from diffsage.config.schema import DiffSageConfig
from diffsage.exceptions.base import ConfigError


def load_config(path: Path) -> DiffSageConfig:
    """Load a configuration file."""

    try:
        with path.open("rb") as file:
            data = tomllib.load(file)

        return DiffSageConfig.model_validate(data)

    except FileNotFoundError as error:
        raise ConfigError(f"Configuration file not found: {path}") from error

    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Invalid TOML syntax: {path}") from error