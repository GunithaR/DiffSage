from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ConfigReport:
    provider: str | None
    model: str | None
    credential_profile: str | None
    timeout: int | None
    max_retries: int | None
    log_level: str | None


@dataclass(slots=True)
class RawConfigReport:
    """Values exactly as written in one config file, which may not be valid settings.

    Shown by `config list --global/--local`, so a broken file can be inspected.
    """

    provider: str | int | None
    model: str | int | None
    credential_profile: str | int | None
    timeout: str | int | None
    max_retries: str | int | None
    log_level: str | int | None


@dataclass(slots=True)
class ConfigSources:
    """Where resolved settings came from, in override order (later wins)."""

    global_file: Path | None = None
    local_file: Path | None = None
    environment: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConfigValueReport:
    key: str
    value: str | int | None
