# ADR-004: HTTPX Instead of Provider SDKs

## Status

Accepted

---

## Context

Many AI providers offer official SDKs.

---

## Decision

Communicate using HTTPX and REST APIs.

---

## Alternatives

- OpenAI SDK
- Anthropic SDK
- Individual provider SDKs

---

## Consequences

Advantages

- Lower dependency count
- Easier provider abstraction
- Consistent implementation across providers