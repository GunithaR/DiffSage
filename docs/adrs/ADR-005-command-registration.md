# ADR-005: Centralized Command Registration

## Status

Accepted

---

## Context

CLI command registration should remain centralized as the number of commands grows.

---

## Decision

Register commands from the CLI layer instead of scattering registration logic across command modules. Accordingly, the new 'pr' command—which automates pull request creation through AI-powered draft generation, interactive editing, and GitHub integration—is registered centrally within the CLI application.

---

## Alternatives

- Decorate each command independently
- Dynamic command discovery

---

## Consequences

The CLI remains the single entry point responsible for application initialization and command registration.