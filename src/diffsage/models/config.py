from dataclasses import dataclass


@dataclass(slots=True)
class ConfigReport:
    provider: str
    model: str
    timeout: int
    max_retries: int
    log_level: str


@dataclass(slots=True)
class ConfigValueReport:
    key: str
    value: str