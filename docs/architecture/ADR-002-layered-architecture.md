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