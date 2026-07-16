# DiffSage Architecture

## Overview

DiffSage is a terminal-first AI-powered Git workflow assistant that helps developers with commit messages, pull requests, merge conflict explanations, code explanations, and other Git-related tasks.

The architecture follows a layered design to separate user interaction, business logic, and infrastructure.

---

# Architecture

```
User
    │
    ▼
CLI (Typer)
    │
    ▼
Commands
    │
    ▼
Services
    │
    ▼
Infrastructure
```

---

# Layer Responsibilities

## CLI

Responsible for:

- Initializing the Typer application
- Registering commands
- Starting the application

Contains no business logic.

---

## Commands

Responsible for:

- Receiving user input
- Validating command arguments
- Calling services
- Displaying terminal output

Commands should never contain business logic.

---

## Services

Responsible for:

- Implementing business logic
- Coordinating providers
- Coordinating Git operations
- Coordinating storage

Services should not directly print to the terminal.

---

## Infrastructure

Infrastructure contains components that communicate with external systems.

Includes:

- Providers
- Git
- Storage
- Logging
- Configuration

---

# Dependency Direction

Dependencies always flow downward.

```
CLI
↓

Commands
↓

Services
↓

Infrastructure
```

Lower layers never depend on upper layers.

---

# Package Structure

```
src/diffsage/
├── commands/
├── services/
├── providers/
├── git/
├── storage/
├── logging/
├── config/
├── core/
└── models/
```

---

# Design Principles

- Separation of concerns
- Single responsibility
- Provider abstraction
- Storage abstraction
- Configuration abstraction
- Replaceable infrastructure
- Terminal-first user experience

---

This document represents the current architecture and should always reflect the latest project structure.