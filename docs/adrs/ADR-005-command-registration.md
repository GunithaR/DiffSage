# ADR-005: Centralized Command Registration

## Status

Accepted

---

## Context

CLI command registration should remain centralized as the number of commands grows.

---

## Decision

Register commands from the CLI layer instead of scattering registration logic across command modules. Additionally, expose a `--version` / `-v` command line option at the CLI entry point to allow users to check the installed version of the tool (updated to 1.3.1).

---

## Alternatives

- Decorate each command independently
- Dynamic command discovery

---

## Consequences

The CLI remains the single entry point responsible for application initialization and command registration.