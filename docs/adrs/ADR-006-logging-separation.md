# ADR-006: Separate Logging from Storage

## Status

Accepted

---

## Context

Logging and persistent storage have different responsibilities.

---

## Decision

Create a dedicated logging package separate from storage.

---

## Alternatives

- Store logging logic inside the storage package

---

## Consequences

Advantages

- Clearer separation of responsibilities
- Easier support for audit logs, application logs, and debug logs
- Logging infrastructure can evolve independently of storage