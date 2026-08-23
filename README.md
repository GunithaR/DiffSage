# DiffSage

> **An AI-aware Git workflow toolkit for developers, automation, and AI agents.**

DiffSage is a modern command-line toolkit that enhances Git workflows with AI while keeping **Git as the single source of truth**. Rather than replacing Git or competing with AI coding assistants, DiffSage provides a reliable, structured interface that helps developers and automation execute Git workflows consistently.

---

## Why DiffSage?

AI coding assistants have dramatically improved code generation, but Git workflows still require reliable execution, proper validation, and consistent handling of repository state.

Today, developers often rely on:

- Manual Git commands
- Shell scripts
- AI-generated terminal commands
- Ad-hoc automation

Each approach solves part of the problem but leaves Git workflow logic scattered across tools.

DiffSage centralizes that logic into a single toolkit.

Instead of reinventing Git operations in every script or AI workflow, developers and automation can invoke DiffSage commands that handle repository validation, Git interactions, AI integration, and workflow execution through a consistent interface.

With the release of version 1.3.1, DiffSage also includes standard CLI options like `--version` (or `-v`) to easily verify the installed version, ensuring predictable behavior across automated environments.

---

# Philosophy

DiffSage is built around several core principles.

### Git remains the source of truth

DiffSage builds on top of Git.

It never replaces Git.

Every operation ultimately delegates to Git while providing a safer and more consistent developer experience.

### AI assists — it doesn't control

Artificial intelligence enhances Git workflows by generating suggestions, summaries, and explanations.

The developer always retains the final decision.

### Reliability over cleverness

Predictable workflows are more valuable than overly complex automation.

Every feature should prioritize correctness, validation, and graceful failure.

### Designed for automation

DiffSage is designed to be consumed by:

- Developers
- Automation scripts
- AI agents

Each consumer interacts through the same consistent interface.

---

# Features

Current capabilities include:

- AI-assisted Conventional Commit generation
- Interactive commit workflow
- Commit message editing using the user's preferred editor
- Commit message regeneration
- Global, local, and resolved configuration management
- Git repository validation
- Environment diagnostics via `diffsage doctor`
- Provider abstraction for AI integrations
- Provider credential management with named profiles
- AI provider authentication and error handling
- Layered architecture
- Comprehensive automated test suite
- Add AI-assisted PR generation
- Interactive PR draft review/edit/regeneration
- GitHub PR creation
- Branch synchronization validation

---

# What DiffSage Is

DiffSage is:

- An AI-aware Git workflow toolkit
- A command-line application
- Git-first
- Automation-friendly
- Extensible through a layered architecture
- Designed for both developers and AI-driven workflows

---

# What DiffSage Is Not

DiffSage is **not**:

- A Git replacement
- A code editor
- A chatbot
- A code generation platform
- A project management tool
- An IDE replacement
- A general-purpose AI assistant

Its scope is intentionally focused on improving Git workflows.

---

# Project Status

> **Current Stage:** Alpha

DiffSage is an actively developed open-source project.

The project is published on PyPI and distributed as a Python package for
developers, automation, and AI agents.

The current focus is on expanding Git workflow capabilities while maintaining
a stable architecture, clear documentation, reliable automation, and strong
engineering practices.

---

# Installation

## User Installation

DiffSage is published on PyPI and can be installed using `pipx`.

DiffSage currently requires Python 3.12.

```bash
pipx install diffsage
```

After installation verify the environment
```bash
diffsage doctor
```

## Developer Installation

Clone the repository:

```bash
git clone <repository-url>
cd DiffSage
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

macOS / Linux

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install the project:

```bash
python -m pip install -e ".[dev]"
```

---

# Releases

DiffSage releases are published through GitHub Releases and distributed through PyPI.

Released package versions can be installed directly with:

```bash
pipx install diffsage
```

A specific version can be installed with:

```bash
pipx install diffsage==1.2.0
```

Release builds and PyPI publishing are automated through GitHub Actions.

---

# Configuration

DiffSage supports layered configuration through global and repository-local TOML files.

Application configuration controls how DiffSage behaves and can be managed through global, repository-local, and environment-based configuration.

Provider credentials are managed separately from application configuration and are not part of the Settings configuration model.

```env
DIFFSAGE_PROVIDER=gemini
DIFFSAGE_AI_MODEL=<provider-supported-model>
DIFFSAGE_LOG_LEVEL=INFO
DIFFSAGE_TIMEOUT=60
DIFFSAGE_MAX_RETRIES=3
```

The configured model must be supported by the selected AI provider.

Configuration can also be managed directly from the CLI:

```bash
diffsage config list
diffsage config get provider
diffsage config set provider gemini
diffsage config unset provider
```

---

# Quick Start

Set up your provider credential:

```bash
diffsage auth set gemini YOUR_API_KEY
```

Verify your environment:

```bash
diffsage doctor
```

View the current configuration:

```bash
diffsage config list
```

Ask the configured AI provider a question:

```bash
diffsage ask "Explain the current staged changes"
```

Generate a commit message:

```bash
diffsage commit
```

Interactive workflow:

```text
Generate commit message
        │
        ▼
Display AI suggestion
        │
        ▼
[Y] Commit
[E] Edit
[R] Regenerate
[N] Cancel
```

```bash
diffsage pr 
```

PR workflow

```text
Generate PR draft
       │
       ▼
Show base/head branches
       │
       ▼
Display PR draft
       │
 ┌─────┼───────────┐
 ▼     ▼           ▼
Edit Regenerate   Cancel
       │
       ▼
    Accept
       │
       ▼
Create GitHub PR
       │
       ▼
Display PR URL
```

Named credential profiles are also supported:

```bash
diffsage auth set gemini YOUR_API_KEY --name paid
```

View configured credentials:

```bash
diffsage auth list
diffsage auth get gemini
```

Remove a credential:

```bash
diffsage auth unset gemini
```

---

# Commands

| Command | Description |
|----------|-------------|
| `diffsage doctor` | Validate the local DiffSage environment |
| `diffsage commit` | Generate and manage AI-assisted commit messages |
| `diffsage pr` | Generate, review, and create a GitHub pull request |
| `diffsage pr <base-branch>` | Generate and create a pull request against a specific base branch |
| `diffsage config list` | Display the current DiffSage configuration |
| `diffsage config get` | Display the value of a configuration setting |
| `diffsage config set` | Update a configuration setting |
| `diffsage config unset` | Remove a configuration setting |
| `diffsage auth set` | Store a provider credential |
| `diffsage auth get` | Display a credential with the API key masked |
| `diffsage auth list` | List configured credentials |
| `diffsage auth unset` | Remove a provider credential |
| `diffsage ask` | Ask the configured AI provider a question |

---

## Pull Request Workflow

The `diffsage pr` command analyzes the current Git branch against a resolved base branch and generates a structured pull request draft.

The workflow is interactive:

```text
Analyze Git repository
        │
        ▼
Resolve base branch
        │
        ▼
Generate PR draft
        │
        ▼
Display base/head branches
        │
        ▼
Review PR draft
        │
 ┌──────┼──────────────┐
 ▼      ▼              ▼
Edit  Regenerate      Cancel
 │      │
 └──────┴───────┐
                ▼
             Accept
                │
                ▼
        Validate GitHub access
                │
                ▼
        Create GitHub pull request
                │
                ▼
        Display pull request URL
```

---

# Architecture Overview

DiffSage follows a layered architecture to separate responsibilities and improve maintainability.

```text
CLI
│
▼
Commands
│
├── Configuration
│
├── Authentication
│
├── Commit Workflow
│
└── Pull Request Workflow
        │
        ▼
    Services
        │
        ├── Git
        ├── GitHub
        ├── AI
        ├── Prompt Generation
        ├── Pull Request Analysis
        ├── Pull Request Parsing
        └── Credentials
        │
        ▼
Providers / Storage
```

Key architectural principles include:

- Single Responsibility Principle
- Separation of concerns
- Dependency inversion
- Provider abstraction
- Testability
- Extensibility

Detailed documentation is available under the `docs/` directory.

---

# Project Structure

```text
src/
└── diffsage/
    ├── commands/
    ├── config/
    ├── exceptions/
    ├── git/
    ├── github/
    ├── logging/
    ├── models/
    ├── parsers/
    ├── prompts/
    ├── providers/
    ├── services/
    ├── storage/
    └── ui/

tests/
├── commands/
├── config/
├── git/
├── github/
├── integration/
├── models/
├── parsers/
├── prompts/
├── providers/
├── services/
├── storage/
└── ui/

docs/
```

---

# Documentation

Additional project documentation is available within the repository.

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | High-level architecture |
| `docs/conventions.md` | Coding conventions and project standards |
| `docs/vision.md` | Project vision and scope |
| `docs/changelog.md` | Project changes and milestones |
| `docs/adrs/ADR-*` | Architecture Decision Records (ADRs) |

---

# Roadmap

The long-term roadmap focuses on strengthening Git workflows rather than expanding into unrelated developer tooling.

Planned capabilities include:

- Pull request generation
- Branch naming assistance
- Merge assistance
- Repository summaries
- Git workflow automation
- Machine-readable output for automation
- Additional AI provider integrations

Every planned feature must satisfy the project's mission:

> **Improve Git workflows while making them more reliable and easier to automate.**

---

# AI-Agent Compatibility

DiffSage is designed to work equally well for humans and automation.

Instead of requiring every automation tool or AI agent to implement Git workflow logic independently, DiffSage provides a reusable interface that encapsulates:

- Repository validation
- Git operations
- GitHub integration
- AI integration
- Workflow execution
- Error handling

This allows developers, scripts, and AI-driven workflows to interact with Git through a consistent, well-defined toolkit.

DiffSage does **not** replace AI coding assistants.

Instead, it complements them by providing reliable Git workflow capabilities.

---

# Design Principles

Every feature in DiffSage should satisfy the following principles:

- Strengthen Git workflows
- Improve workflow reliability
- Simplify automation
- Preserve human control
- Maintain architectural consistency

Features that fall outside these principles intentionally remain out of scope.

---

# Contributing

DiffSage is an open-source project and contributions are welcome.

Before contributing, review the project architecture, coding conventions, and architectural decision records in the `docs/` directory.

Additional contribution guidelines will be documented as the project evolves.

---

# License

This project is licensed under the MIT License.

See the `LICENSE` file for details.