# ADR-002: Layered Architecture

## Status

Accepted

---

## Context

Business logic should not be mixed with user interaction or infrastructure.

---

## Decision

Adopt four layers.

```
CLI
↓

Commands
↓

Services
↓

Infrastructure
```

Services communicate using structured domain models rather than raw subprocess output, provider-specific responses, or terminal-facing text. Each layer exposes abstractions appropriate to its responsibility. To support real-time UI feedback (such as retry attempts during generation) without coupling lower layers to presentation concerns, operations may accept optional progress tracking callbacks.

---

## Alternatives

- Flat architecture
- MVC

---

## Consequences

Advantages

- Easier testing
- Better maintainability
- Clear separation of concerns
- Layers remain independent through well-defined domain models.
- Infrastructure implementations can change without affecting service logic.
---