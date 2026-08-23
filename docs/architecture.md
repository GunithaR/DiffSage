# DiffSage Architecture

## Overview

DiffSage is a terminal-first AI-powered Git workflow toolkit that helps
developers with AI-assisted Git workflows while providing configuration,
authentication, diagnostics, and extensible provider integrations.

The architecture follows a layered design to separate user interaction,
business logic, and infrastructure while keeping Git workflow operations
independent from provider-specific AI implementations.

DiffSage uses Git as the primary source of truth for Git workflow operations.
AI-generated content is derived from structured Git evidence and remains
subject to user review before workflow actions are performed.

---

# Architecture

```text
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
- Registering commands and global options (such as `--version`/`-v` to display the current package version, 1.3.1)
- Starting the application

Contains no business logic.

---

## Commands

Responsible for:

- Receiving user input and command-line options
- Validating command arguments
- Composing application dependencies
- Calling services
- Handling domain exceptions
- Displaying terminal output through Views

Commands should not implement business logic.

---

## Services

Responsible for:

- Implementing business logic
- Coordinating AI providers
- Coordinating Git operations
- Coordinating GitHub operations
- Coordinating storage
- Performing validation
- Returning structured domain models

**Services should not directly print to the terminal.**

Services communicate using structured report models rather than terminal output, 
raw subprocess output, provider-specific JSON, or formatted terminal text whenever practical.

Services perform validation, normalization, and orchestration while remaining
independent of the presentation layer.

---

## Infrastructure

Infrastructure contains components that communicate with external systems or
provide persistence and application infrastructure.

Includes:

- Providers
- Git
  - Provides the low-level interface for repository operations.
  - Responsibilities include:
    - Reading repository state
    - Reading branch information
    - Reading commits
    - Reading diffs
    - Determining merge bases
    - Reading remote branch state
  - Git remains the primary source of truth for Git workflow analysis.
- GitHub
  - Provides integration with GitHub through the GitHub CLI.
  - Responsibilities include:
    - Checking GitHub CLI availability
    - Checking GitHub CLI authentication
    - Creating pull requests
  - GitHub operations are kept separate from Git repository analysis.
- Storage
- Repositories
  - Persist configuration and credentials
  - Read persisted data
  - No business logic
  - No validation
- Logging
  - Centralized initialization
  - Console handler
  - File handler
  - Configurable log level
- Configuration
  - Loads and resolves application configuration
  - Supports global, local, and environment-based configuration
- Authentication
  - Resolves provider credentials
  - Persists credential profiles separately from application configuration

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
    ├──────────────► Configuration
    │
    ├──────────────► Authentication
    │                       │
    │                       ▼
    │                 Credential Store
    │
    ├──────────────► Git
    │
    ├──────────────► GitHub
    │
    ▼
Provider / Repository
    │
    ▼
Runtime Models
    │
    ▼
Report / Domain Models
    │
    ▼
View
```

## Responsibilities

### Commands

- Receiving user input
- Composing application dependencies
- Calling services
- Handling domain exceptions
- Control interactive workflow
- Delegating terminal output to views

### Services

- Implement business logic.
- Validate and normalize user input.
- Coordinate repositories and providers.
- Coordinate Git and GitHub operations.
- Return structured report models.
- Never perform terminal output.

### Repositories

- Persist and retrieve application data.
- Encapsulate storage implementation details.
- Contain no business logic or validation.

### Authentication

- Resolve credentials for the configured provider and profile.
- Keep provider credentials separate from application configuration.
- Provide credential data to provider implementations.
- Raise domain-specific errors when required credentials are unavailable.

### Providers

- Communicate with external AI services.
- Translate provider-specific responses into common domain models.
- Hide provider implementation details from higher layers.

### Git

- Provide repository state and history
- Collect branch, commit, diff, and remote information
- Remain independent of AI and GitHub-specific logic

### GitHub

- Integrate with GitHub through the GitHub CLI
- Validate CLI availability and authentication
- Create pull requests from validated repository state

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


---

# AI Request Flow

LLM-enabled Git workflows use the service layer to coordinate Git context,
prompt generation, credential resolution, and provider communication.

```text
Command
    │
    ▼
CommitService / PullRequestService
    │
    ├── GitService
    │      │
    │      ▼
    │   CommitContext / PullRequestContext
    │
    ├── PromptService
    │
    └── AIService
           │
           ├── CredentialService
           │      │
           │      ▼
           │   CredentialsRepository
           │
           └── Provider Factory
                  │
                  ▼
              BaseProvider
                  │
                  ▼
          Provider Implementation
                  │
                  ▼
          ProviderResponse
```

Responsibilities:

- **GitService** collects repository information and returns structured domain models.
- **PromptService** transforms domain models into prompts for language models.
- **AIService** coordinates AI requests, credential resolution, provider selection, and retry handling.
- **CredentialService** resolves provider credentials through the credential repository.
- **BaseProvider** defines the common provider contract.
- **Provider implementations** communicate with external LLM APIs and normalize provider-specific responses into `ProviderResponse`.
- **Commands** orchestrate the application workflow, handle domain errors, and present results to the user.

This separation keeps Git logic, prompt generation, authentication, AI orchestration, and provider-specific implementations independent.

---

# Commit Workflow

The commit workflow uses Git repository state to generate an AI-assisted
commit message. DiffSage analyzes the staged changes and relevant commit
history, generates a structured commit message, and allows the user to review
and edit the result before committing.

```text
Command
    │
    ▼
GitService
    │
    ├── Current Branch
    ├── Staged Diff
    ├── Unstaged Diff
    └── Recent Commits
    │
    ▼
CommitContext
    │
    ▼
PromptService
    │
    ▼
AIService
    │
    ▼
Commit Message
    │
    ▼
Commit Review
    │
    ├── Accept
    ├── Edit
    ├── Regenerate
    └── Cancel
    │
    ▼
GitClient
    │
    ▼
Git Commit
```

## Commit Responsibilities

### GitService

GitService provides the repository evidence required for commit message
generation.

It is responsible for:
- Determining the current branch
- Collecting staged changes
- Collecting unstaged changes
- Collecting recent commit history
- Building the CommitContext

### CommitService

CommitService coordinates commit message generation.

It combines:
- GitService
- PromptService
- AIService

The service validates that:
- The current directory is a Git repository
- Staged changes are available

It then builds the commit context, generates the AI prompt, and returns the
generated commit message.

### PromptService

Transforms the CommitContext into the prompt supplied to the AI provider.

The prompt uses repository evidence rather than relying on user-provided
descriptions of the changes.

### AIService

Coordinates the AI request and provider interaction required to generate the
commit message.

### EditorService

Allows the user to manually edit a generated commit message before accepting
it.

### GitClient

Performs the final Git commit after the user accepts the generated message.

---

# Commit Data Flow

The commit workflow uses structured models between layers.

```text
Git Repository
      │
      ▼
CommitContext
      │
      ▼
PromptService
      │
      ▼
AIService
      │
      ▼
Generated Commit Message
      │
      ▼
User Review
      │
      ├── Accept ───────► GitClient ───► Git Commit
      ├── Edit ─────────► Review Again
      ├── Regenerate ───► AIService
      └── Cancel
```

The CommitContext contains:

- current branch
- staged diff
- unstaged diff
- recent commits

The generated commit message remains subject to user review before the Git
commit is executed.

---

# Pull Request Workflow

The pull request workflow follows a Git-first architecture.

Git repository state is collected and analyzed before AI generation. The
generated pull request draft is treated as a proposal and must be reviewed by
the user before a pull request is created.

```text
Command
    │
    ▼
GitService
    │
    ├── Current Branch
    ├── Base Branch
    ├── Merge Base
    ├── Branch Commits
    ├── Changed Files
    └── Git Diff
    │
    ▼
PullRequestContext
    │
    ▼
PullRequestAnalysisService
    │
    ▼
Deterministic Analysis
    │
    ▼
PromptService
    │
    ▼
AIService
    │
    ▼
PullRequestParser
    │
    ▼
PullRequestDraft
    │
    ▼
Pull Request Review
    │
    ├── Accept
    ├── Edit
    ├── Regenerate
    └── Cancel
    │
    ▼
GitHubService
    │
    ├── GitHub CLI Availability
    ├── GitHub Authentication
    └── Remote Branch Validation
    │
    ▼
GitHubClient
    │
    ▼
GitHub CLI
    │
    ▼
GitHub Pull Request
```

---

# Pull Request Responsibilities

## GitService

GitService provides the repository evidence required for pull request
generation.

It is responsible for:
- Resolving the base branch
- Determining the current branch
- Determining the merge base
- Collecting branch commits
- Collecting changed files
- Collecting the branch diff
- Validating remote branch synchronization

## PullRequestAnalysisService

Performs deterministic analysis of the Git repository evidence.

Analysis provides structured signals such as:
- Risk classification
- Reviewer focus
- Change characteristics
- Other deterministic repository signals

Deterministic analysis supports AI generation but does not replace inspection
of the actual Git diff.

## PullRequestService

Coordinates pull request draft generation.

It combines:
- GitService
- PullRequestAnalysisService
- PromptService
- AIService
- PullRequestParser

The service returns a validated PullRequestDraft.

## PullRequestParser

Converts AI-generated or user-edited structured content into a validated
PullRequestDraft.

The parser ensures that edited drafts conform to the expected structure before
they are accepted by the workflow.

## EditorService

Provides interactive editing of pull request drafts.

Drafts are serialized into JSON before being passed to the user’s editor.

Edited content is parsed and validated before replacing the current draft.

Invalid edits do not terminate the workflow. The user can return to the edit
workflow and provide corrected content.

## GitHubService

Coordinates pull request creation and performs GitHub-specific validation.

Before creation it verifies:
- GitHub CLI availability
- GitHub CLI authentication
- Remote branch existence
- Local branch synchronization with the remote branch

The service then delegates actual pull request creation to GitHubClient.

## GitHubClient

Provides the low-level GitHub CLI interface.

It is responsible for:
- Executing GitHub CLI commands
- Checking gh availability
- Checking gh authentication
- Creating pull requests

GitHub-specific subprocess behavior remains isolated from the command and
service layers.

---

# Pull Request Data Flow

The pull request workflow uses structured models between layers.

```text
Git Repository
      │
      ▼
PullRequestContext
      │
      ▼
PullRequestAnalysis
      │
      ▼
AI Prompt
      │
      ▼
ProviderResponse
      │
      ▼
PullRequestParser
      │
      ▼
PullRequestDraft
      │
      ▼
GitHubService
      │
      ▼
Pull Request URL
```

## The PullRequestDraft contains:
- title
- summary
- why
- changes
- testing
- risks
- reviewer_focus
- breaking_changes

The draft is independent of terminal presentation and GitHub API/CLI
representation.

---

# Git-First Pull Request Creation

DiffSage does not create a pull request directly from unverified local state.

Before pull request creation, the current branch must be synchronized with its
remote branch.

```text
Local Branch
    │
    ▼
Current Commit
    │
    ▼
Remote Branch
    │
    ▼
Synchronization Validation
    │
    ├── Synchronized ───────► Continue
    │
    └── Not Synchronized ──► Reject PR Creation
```

This prevents DiffSage from creating a pull request whose remote branch does
not contain the commits used to generate the pull request draft.

Git remains the source of truth for the repository state, while GitHub is used
as the destination for the resulting pull request.

---

# Interactive Pull Request Review

The pull request command uses an interactive review loop.

```text
Generate Draft
      │
      ▼
Display Draft
      │
      ▼
User Choice
      │
 ┌────┼───────────────┐
 │    │       │       │
 ▼    ▼       ▼       ▼
Accept Edit  Regenerate Cancel
 │    │       │
 │    ▼       ▼
 │  Validate Generate
 │    │       │
 │    └───┬───┘
 │        │
 │        ▼
 │   Display Draft
 │        │
 └────────┘
      │
      ▼
GitHub Validation
      │
      ▼
Create Pull Request
```

This keeps the developer in control of AI-generated content and ensures that
AI suggestions are reviewed before external workflow actions are performed.

---

# Error Handling

DiffSage uses project-specific exceptions for expected domain failures.

Pull request workflows may encounter errors including:
- NotGitRepositoryError
- DetachedHeadError
- BaseBranchNotFoundError
- SameBranchError
- RemoteBranchNotFoundError
- UnpushedChangesError
- GitHubCLIUnavailableError
- GitHubAuthenticationError
- InvalidPullRequestDraftError
- ProviderError
- CredentialNotFoundError
- ConfigError

Commands translate these domain errors into user-facing terminal messages
through the appropriate View.

Unexpected errors are logged for diagnostics while the user receives a
generic error message.

---

# Package Structure

```
src/diffsage/
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
- Git-first workflow design
- GitHub integration isolated from Git analysis
- Human review of AI-generated workflow content
- Report models separating business and presentation
- Hierarchical configuration resolution
- Authentication separated from configuration
- Deterministic analysis supporting AI generation

---

This document represents the current architecture and should always reflect the latest project structure.