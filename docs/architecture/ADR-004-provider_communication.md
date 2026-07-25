# ADR-004: Provider SDKs Behind an Abstraction Layer

## Status

Accepted

---

## Context

DiffSage integrates with multiple AI providers such as Google Gemini, OpenAI, Anthropic, and local models.

There are two primary implementation approaches:

- Use raw HTTP clients (e.g., HTTPX) and manually communicate with each provider's REST API.
- Use the provider's official SDK.

The project architecture already isolates provider-specific implementations behind the `BaseProvider` interface. This abstraction prevents the rest of the application from depending on any specific provider implementation.

---

## Decision

Provider implementations may use either:

- an official provider SDK, or
- a direct HTTP client,

provided that all provider-specific details remain encapsulated within the provider layer.

The rest of the application communicates only through:

- `ProviderRequest`
- `ProviderResponse`
- `BaseProvider`

No SDK-specific types or exceptions may cross the provider boundary.

---

## Alternatives Considered

### Option 1 – HTTPX for all providers

Pros

- Uniform implementation style
- Lower dependency count
- Full control over HTTP requests

Cons

- More boilerplate
- Manual request/response serialization
- Manual authentication handling
- Responsibility for API compatibility

---

### Option 2 – Official SDKs (Selected)

Pros

- Officially supported
- Less boilerplate
- Better compatibility with provider updates
- Simpler authentication
- Faster feature adoption

Cons

- Additional dependency
- Different SDK APIs between providers

The provider abstraction layer prevents these differences from affecting the rest of the application.

---

## Consequences

Advantages

- Provider SDKs remain implementation details.
- The application remains provider-agnostic.
- Providers can be replaced without changing commands, services, or models.
- Official SDKs reduce maintenance burden while preserving architectural boundaries.

Trade-offs

- Provider implementations are no longer identical internally.
- Each provider may use a different SDK or HTTP implementation.
- Additional dependencies are introduced, but they remain isolated to the provider layer.