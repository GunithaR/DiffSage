from dataclasses import dataclass
from datetime import time

@dataclass(slots=True)
class ProviderRequest:
    prompt: str
    model: str
    temperature: float
    max_tokens: int

@dataclass(slots=True)
class ProviderResponse:
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    finish_reason: str
    latency_ms: int