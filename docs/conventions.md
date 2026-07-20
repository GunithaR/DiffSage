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

- Never use print()
- Use typer.echo() for user-facing terminal output.
- Use get_logger() for application logging.
- configure_logging() must only be called once during application startup.

---

## Exceptions

Never raise generic Exception.

Always raise a project-specific exception.

Example:

- ConfigError
- ProviderError
- GitError

---

## Configuration

Commands should never load configuration directly.

Services should receive configuration through the Settings model or dedicated abstractions.

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

## Code Quality

Before committing:

- ruff check . --fix
- ruff format .
- ruff check .
- ruff format --check .

---

## Testing

Every new service should have corresponding unit tests.

---

These conventions should evolve with the project.