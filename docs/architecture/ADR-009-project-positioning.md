# ADR-009: Project Positioning

- **Status:** Accepted
- **Date:** 2026-07-26

---

# Context

DiffSage was initially conceived as an AI-powered Git assistant capable of generating commit messages and simplifying common Git tasks.

As the project evolved, its architecture became increasingly modular, introducing:

- A layered architecture
- Git service abstraction
- AI provider abstraction
- Centralized configuration
- Structured models
- Comprehensive testing
- Command-oriented workflows

During this evolution, it became clear that the project's architecture supported a broader and more sustainable goal than simply providing AI-generated commit messages.

At the same time, the software development ecosystem has seen rapid growth in AI coding assistants and autonomous development tools. These systems increasingly require reliable mechanisms for interacting with Git repositories, yet frequently duplicate Git workflow logic or rely on ad hoc shell commands.

This raised an important architectural question:

> Should DiffSage evolve into another AI coding assistant, or should it provide a reliable Git workflow layer that complements existing developer tools and AI systems?

---

# Decision

DiffSage will be positioned as an **AI-aware Git workflow toolkit**.

Its primary responsibility is to provide reliable, consistent, and extensible Git workflow capabilities for developers, automation, and AI agents.

DiffSage builds upon Git rather than replacing it and integrates AI where it meaningfully enhances Git workflows.

The project intentionally avoids becoming a general-purpose AI coding assistant.

---

# Rationale

This positioning aligns naturally with the existing architecture.

The project's service-oriented design, provider abstraction, and Git integration already separate Git workflow concerns from AI implementation details.

Rather than competing with AI coding assistants, DiffSage complements them by providing a reusable interface for Git operations and workflow execution.

This allows:

- Developers to perform Git workflows more efficiently.
- Automation scripts to reuse consistent Git logic.
- AI agents to invoke Git workflows without implementing Git-specific behavior themselves.

By focusing on Git workflows, DiffSage maintains a clear and sustainable project scope.

---

# Consequences

## Positive

- Clearly defined project identity.
- Reduced scope creep.
- Architecture aligns with project goals.
- Easier integration with automation and AI systems.
- Improved long-term maintainability.
- Distinct positioning within the developer tooling ecosystem.

## Negative

- Features unrelated to Git workflows will intentionally remain out of scope.
- DiffSage will not compete directly with AI coding assistants that provide code generation or conversational capabilities.

---

# Scope Definition

## In Scope

- Commit workflows
- Branch workflows
- Pull request assistance
- Merge assistance
- Repository analysis
- Git diagnostics
- AI-assisted Git operations
- Workflow automation
- Machine-readable outputs for automation
- AI provider integrations that improve Git workflows

---

## Out of Scope

- Code generation
- Bug fixing
- Code review
- IDE replacement
- Chat interfaces
- Project management
- General-purpose AI tooling
- DevOps orchestration unrelated to Git workflows

---

# Design Principles

Future features should reinforce one or more of the following principles:

- Improve Git workflows.
- Increase workflow reliability.
- Simplify automation.
- Preserve human control.
- Maintain architectural consistency.
- Keep Git as the source of truth.

Features that do not support these principles should generally be considered outside the project's scope.

---

# Alternatives Considered

## Continue as an AI Git assistant

This approach would focus primarily on AI-generated commit messages and interactive developer assistance.

Rejected because it underutilizes the project's architecture and overlaps significantly with existing AI coding assistants.

---

## Become a general-purpose AI development platform

This approach would expand DiffSage into code generation, code review, project management, and other AI-assisted development tasks.

Rejected because it significantly broadens the project's scope, increases maintenance complexity, and dilutes its primary mission.

---

## Position DiffSage as an AI-aware Git workflow toolkit (Selected)

This approach establishes DiffSage as a focused developer tool that provides reliable Git workflow capabilities while remaining compatible with developers, automation, and AI systems.

This option best aligns with the project's architecture, long-term maintainability, and design philosophy.

---

# References

- `README.md`
- `docs/vision.md`
- `docs/architecture.md`
- ADR-001 through ADR-008