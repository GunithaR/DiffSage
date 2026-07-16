# ADR-003: Storage Abstraction

## Status

Accepted

---

## Context

Persistent data may evolve from JSON files to SQLite or another storage backend.

---

## Decision

Introduce a Storage layer with a common abstraction.

---

## Alternatives

- Direct JSON access throughout the application
- SQLite from the beginning

---

## Consequences

Business logic remains independent of the storage implementation.