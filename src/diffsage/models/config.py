from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ConfigReport:
    provider: str | None
    model: str | None
    timeout: int | None
    max_retries: int | None
    log_level: str | None


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
