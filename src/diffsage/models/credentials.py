from dataclasses import dataclass


@dataclass(slots=True)
class Credential:
    provider: str
    name: str
    api_key: str