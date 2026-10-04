import tomllib
from pathlib import Path

from pydantic import ValidationError

from diffsage.config.paths import display_path
from diffsage.config.schema import PartialDiffSageConfig
from diffsage.exceptions import ConfigError


def _describe_validation_error(error: ValidationError) -> str:
    """Summarise pydantic errors as 'section.key: problem (got value)'."""

    problems = []

    for detail in error.errors():
        location = ".".join(str(part) for part in detail["loc"])
        problem = f"{location}: {detail['msg']}"

        if "input" in detail and not isinstance(detail["input"], dict):
            problem += f" (got {detail['input']!r})"

        problems.append(problem)

    return "; ".join(problems)


def load_config(path: Path) -> PartialDiffSageConfig:
    """Load a configuration file."""

    try:
        with path.open("rb") as file:
            data = tomllib.load(file)

    except FileNotFoundError as error:
        raise ConfigError(f"Configuration file not found: {display_path(path)}") from error

    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Invalid TOML syntax in {display_path(path)}: {error}") from error

    except OSError as error:
        raise ConfigError(
            f"Cannot read configuration file {display_path(path)}: {error.strerror}"
        ) from error

    try:
        return PartialDiffSageConfig.model_validate(data)

    except ValidationError as error:
        raise ConfigError(
            f"Invalid configuration in {display_path(path)}: {_describe_validation_error(error)}"
        ) from error
