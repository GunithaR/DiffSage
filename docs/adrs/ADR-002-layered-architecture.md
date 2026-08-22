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

Services communicate using structured domain models rather than raw subprocess output, provider-specific responses, or terminal-facing text. Each layer exposes abstractions appropriate to its responsibility. For example, the `pr` command is registered in the CLI layer, orchestrates execution in the Commands layer, utilizes Services for AI-powered draft generation and interactive editing, and relies on the Infrastructure layer for GitHub pull request creation.

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