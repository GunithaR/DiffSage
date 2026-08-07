# DiffSage Architecture

## Overview

DiffSage is a terminal-first AI-powered Git workflow toolkit that helps developers with commit messages, pull requests, merge conflict explanations, code explanations, and other Git-related tasks.

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
Application Initialization
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

Services communicate using structured report models rather than terminal output.

Services perform validation, normalization, and orchestration while remaining
independent of the presentation layer.

---

## Infrastructure

Infrastructure contains components that communicate with external systems.

Includes:

- Providers
- Git
- Storage
- Repositories
    - Persist configuration
    - Read configuration
    - No business logic
    - No validation
- Logging
    - Centralized initialization
    - Console handler
    - File handler
    - Configurable log level
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

Services exchange structured data using models (DTOs), allowing commands to focus on presentation while services focus on business logic.

---

# Runtime Request Flow

Most DiffSage features follow a common execution pipeline.

```text
Command
    │
    ▼
Service
    │
    ▼
Repository / Provider
    │
    ▼
Runtime Models
    │
    ▼
Report Models
    │
    ▼
View
```

## Responsibilities

### Commands

- Receive user input.
- Compose application dependencies.
- Invoke services.
- Handle domain exceptions.
- Delegate presentation to views.

### Services

- Implement business logic.
- Validate and normalize user input.
- Coordinate repositories and providers.
- Return structured report models.
- Never perform terminal output.

### Repositories

- Persist and retrieve application data.
- Encapsulate storage implementation details.
- Contain no business logic or validation.

### Providers

- Communicate with external AI services.
- Translate provider-specific responses into common domain models.
- Hide provider implementation details from higher layers.

### Runtime Models

- Represent internal application data.
- Transfer information between infrastructure and services.
- Remain independent of presentation concerns.

### Report Models

- Represent data prepared for presentation.
- Separate business logic from the user interface.
- Provide a stable interface between services and views.

### Views

- Render Rich terminal output.
- Display reports returned by services.
- Never contain business logic.
```

---

# AI Request Flow

LLM-enabled features follow the same layered architecture.

```
Command
    │
    ▼
GitService
    │
    ▼
CommitContext
    │
    ▼
PromptService
    │
    ▼
BaseProvider
    │
    ▼
ProviderResponse
```

Responsibilities:

- **GitService** collects repository information and returns structured domain models.
- **PromptService** transforms domain models into prompts for language models.
- **BaseProvider** defines the common provider contract.
- **Provider implementations** communicate with external LLM APIs and normalize provider-specific responses into `ProviderResponse`.
- **Commands** orchestrate the workflow and present results to the user.

This separation keeps Git logic, prompt generation, and provider implementations independent.

---

# Package Structure

```
src/diffsage/
├── commands/
├── config/
├── exceptions/
├── git/
├── logging/
├── models/
├── parsers/
├── prompts/
├── providers/
├── services/
├── storage/
└── ui/
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
- Domain model driven communication between layers
- Constructor-based dependency injection
- Repository pattern
- Report models separating business and presentation
- Hierarchical configuration resolution
- Authentication separated from configuration

---

This document represents the current architecture and should always reflect the latest project structure.