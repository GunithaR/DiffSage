# ADR-008: Provider Response Normalization

## Status

Accepted

---

## Context

Each LLM provider exposes different response formats and metadata.

Returning provider-specific responses throughout the application would tightly couple business logic to individual providers.

---

## Decision

Normalize provider responses into a common `ProviderResponse` domain model before returning them from provider implementations.

---

## Alternatives

- Return raw provider JSON.
- Return only generated text.
- Create provider-specific response models throughout the application.

---

## Consequences

Advantages

- Business logic remains independent of provider APIs.
- Metadata such as model name, token usage, finish reason, and latency become consistently available.
- Simplifies provider fallback and telemetry.
- New providers require changes only within their own implementation.

Disadvantages

- Provider implementations perform an additional mapping step.