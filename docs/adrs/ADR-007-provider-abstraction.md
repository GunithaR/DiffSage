# ADR-007: Provider Abstraction

## Status

Accepted

---

## Context

DiffSage supports multiple LLM providers. Business logic should not depend on a specific provider implementation.

---

## Decision

Introduce a common `BaseProvider` abstraction.

All provider implementations inherit from this abstraction and expose a common interface to the service layer.

---

## Alternatives

- Provider-specific implementations throughout the application
- Conditional logic based on provider names

---

## Consequences

Advantages

- Providers become interchangeable.
- New providers can be added with minimal changes.
- Business logic remains provider-agnostic.
- Easier testing through mock provider implementations.

Disadvantages

- Requires maintaining a shared provider contract.