from dataclasses import dataclass


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
    # None when the provider does not report usage or a finish reason.
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    latency_ms: int
