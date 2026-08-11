from dataclasses import dataclass


@dataclass(slots=True)
class ConfigReport:
    provider: str | None
    model: str | None
    timeout: int | None
    max_retries: int | None
    log_level: str | None


@dataclass(slots=True)
class ConfigValueReport:
    key: str
    value: str | int | None
