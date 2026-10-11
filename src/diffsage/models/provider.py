from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ProviderRequest:
    prompt: str
    model: str
    temperature: float
    max_tokens: int
    # JSON Schema the reply must follow. Providers with a structured-output mode
    # enforce it; the caller still validates the reply.
    response_schema: dict[str, Any] | None = None


@dataclass(slots=True)
class ProviderResponse:
    content: str
    provider: str
    model: str
    # None when the provider does not report usage or a finish reason.
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    latency_ms: int
