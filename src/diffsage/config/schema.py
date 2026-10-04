"""Configuration schema: the single source of truth for valid DiffSage settings.

Config files, DIFFSAGE_* environment variables and `diffsage config set` are all
validated against these models, so the same value is accepted or rejected everywhere.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 600
MIN_RETRIES = 0
MAX_RETRIES = 10

# CLI key -> (config file section, option)
CONFIG_KEYS: dict[str, tuple[str, str]] = {
    "provider": ("ai", "provider"),
    "model": ("ai", "model"),
    "credential_profile": ("ai", "credential_profile"),
    "timeout": ("network", "timeout"),
    "max_retries": ("network", "max_retries"),
    "log_level": ("logging", "level"),
}


def _lower(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


def _upper(value: Any) -> Any:
    return value.strip().upper() if isinstance(value, str) else value


Provider = Annotated[Literal["gemini"], BeforeValidator(_lower)]
Model = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Profile names are stored lowercased by `diffsage auth set --name`.
CredentialProfile = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)
]
Timeout = Annotated[int, Field(ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)]
MaxRetries = Annotated[int, Field(ge=MIN_RETRIES, le=MAX_RETRIES)]
LogLevel = Annotated[
    Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], BeforeValidator(_upper)
]


class _Section(BaseModel):
    # A misspelled key or section is an error, not silently ignored.
    model_config = ConfigDict(extra="forbid")


class AIConfig(_Section):
    provider: Provider
    model: Model
    credential_profile: CredentialProfile


class NetworkConfig(_Section):
    timeout: Timeout
    max_retries: MaxRetries


class LoggingConfig(_Section):
    level: LogLevel


class DiffSageConfig(_Section):
    ai: AIConfig
    network: NetworkConfig
    logging: LoggingConfig


class PartialAIConfig(_Section):
    provider: Provider | None = None
    model: Model | None = None
    credential_profile: CredentialProfile | None = None


class PartialNetworkConfig(_Section):
    timeout: Timeout | None = None
    max_retries: MaxRetries | None = None


class PartialLoggingConfig(_Section):
    level: LogLevel | None = None


class PartialDiffSageConfig(_Section):
    ai: PartialAIConfig | None = None
    network: PartialNetworkConfig | None = None
    logging: PartialLoggingConfig | None = None
