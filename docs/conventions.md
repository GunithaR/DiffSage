# Coding Conventions

## Naming

Packages:
- snake_case

Modules:
- snake_case

Classes:
- PascalCase

Functions:
- snake_case

Constants:
- UPPER_CASE

Variables:
- snake_case

---

## Type Hints

All public functions should include type hints.

Example

```python
def doctor() -> None:
```

---

## Docstrings

Write docstrings only when they provide meaningful documentation.

Avoid docstrings that merely repeat the code.

---

## Imports

Import order:

1. Standard library
2. Third-party packages
3. Local project imports

Separate each group with a blank line.

---

## Logging

Never use print().

Use:

- typer.echo() for terminal output
- logging package for application logs

---

## Exceptions

Never raise generic Exception.

Always raise a project-specific exception.

Example:

- ConfigError
- ProviderError
- GitError

---

## Services

Services must not interact directly with the terminal.

---

## Commands

Commands may:

- Read user input
- Display output

Commands must not implement business logic.

---

## Testing

Every new service should have corresponding unit tests.

---

These conventions should evolve with the project.