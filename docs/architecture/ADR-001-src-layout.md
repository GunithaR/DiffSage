# ADR-001: Use src Layout

## Status

Accepted

---

## Context

Python packages can either be placed directly in the project root or inside a dedicated src directory.

---

## Decision

Use the src layout.

```
src/
    diffsage/
```

---

## Alternatives

- Flat project layout

---

## Consequences

Advantages

- Prevents accidental imports
- Better package isolation
- Standard modern Python packaging
- Cleaner editable installs
- Easier PyPI publishing

Disadvantages

- Slightly more configuration required