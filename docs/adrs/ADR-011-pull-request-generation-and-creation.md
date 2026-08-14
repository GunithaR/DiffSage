# ADR-011: Git-First Pull Request Generation and Creation

- **Status:** Accepted
- **Date:** 2026-08-14

---

## Context

DiffSage currently provides an AI-assisted commit workflow that uses Git repository state as the primary source of truth.

The next major workflow capability is pull request generation and creation.

A pull request represents a larger unit of change than an individual commit. Generating a useful pull request therefore requires understanding the complete branch change rather than relying only on the latest commit message.

DiffSage must collect factual information from Git and the repository before generating pull request content. AI should interpret this information and produce useful reviewer-facing content without becoming the source of truth.

The feature must also support creation of the resulting pull request through a Git hosting platform while keeping hosting-specific implementation details separate from the core workflow logic.

The initial implementation targets GitHub.

---

## Decision

DiffSage will implement a Git-first pull request generation and creation workflow.

Git remains the primary source of truth for repository state and change information.

The workflow will follow this general pipeline:

```text
Git Repository
      │
      ▼
Branch / PR Context Collection
      │
      ├── Current branch
      ├── Base branch
      ├── Merge base
      ├── Commit history
      ├── Changed files
      └── Branch diff
      │
      ▼
Deterministic Analysis
      │
      ├── Changed areas
      ├── Risk signals
      └── Reviewer focus signals
      │
      ▼
Repository Context
      │
      ├── PR template
      └── Relevant repository conventions
      │
      ▼
AI Service
      │
      ▼
Structured Pull Request Draft
      │
      ▼
Preview / Edit / Regenerate / Confirm
      │
      ▼
Git Hosting Service
      │
      ▼
GitHub Pull Request
```

AI-generated content must be grounded in repository evidence collected by DiffSage.

Deterministic analysis is responsible for producing factual signals from the repository. The AI layer is responsible for transforming those signals into human-readable pull request content.

The AI must not be treated as the source of truth for repository state.

---

## Initial Feature Scope

The first implementation of pull request generation and creation will include:

- Current branch detection.
- Base branch resolution.
- Merge-base calculation.
- Branch commit history collection.
- Changed-file collection.
- Full branch diff collection.
- Repository state validation.
- Detection and use of repository pull request templates where available.
- Use of relevant repository conventions where available.
- Deterministic analysis of changed areas.
- Deterministic risk signals and risk classification.
- Reviewer focus signals derived from changed repository areas.
- Structured AI-generated pull request drafts.
- Pull request preview before creation.
- Manual editing of generated pull request content.
- Pull request regeneration.
- User confirmation before creation.
- GitHub pull request creation.
- Detection of an existing pull request for the current branch.

The initial user-facing command will be:

```bash
diffsage pr
```

The command should follow the interaction model already established by the `diffsage commit` workflow.

---

## Pull Request Draft Model

Generated pull requests will be represented using a structured domain model rather than an arbitrary block of generated Markdown.

The initial model should support:

- Title
- Summary
- Why
- Changes
- Testing evidence
- Risks
- Reviewer focus
- Breaking changes

The exact presentation may evolve independently from the domain model.

This allows services, views, and hosting integrations to operate on structured data rather than provider-specific or presentation-specific text.

---

## Git Context

Pull request generation will use Git as the authoritative source of repository change information.

The pull request context should include at least:

- Current branch
- Base branch
- Merge base
- Commits included in the branch
- Changed files
- Branch diff

Base branch resolution must be deterministic.

The system must not rely on the language model to determine whether a branch should be compared against `main`, `master`, or another branch.

The implementation must explicitly handle conditions such as:

- Not being inside a Git repository.
- Detached HEAD state.
- Missing Git remote configuration.
- Missing upstream information.
- Unable to determine a valid base branch.
- Existing pull requests for the current branch.

---

### Base Branch Selection

The `diffsage pr` command supports an optional base branch argument.

When no base branch is supplied, DiffSage will deterministically resolve the
repository's default base branch.

When a base branch is supplied, DiffSage will use that branch explicitly.

Examples:

```bash
diffsage pr
diffsage pr develop
diffsage pr release/2.0
```

The current branch is always treated as the source branch. The supplied branch
is treated as the target/base branch.

The AI layer must not determine or override the selected base branch.

---

## Deterministic Analysis

Facts about the repository must be derived from deterministic analysis rather than generated by the AI model.

Initial deterministic analysis may include:

- Changed directories and modules.
- Authentication-related changes.
- Configuration-related changes.
- Provider-related changes.
- Dependency changes.
- Public interface changes.
- Test changes.
- Documentation-only changes.

Risk classification should be based on deterministic signals.

For example, changes affecting authentication, configuration, provider implementations, dependencies, or public interfaces may increase risk.

AI may explain the resulting risk classification in human-readable language, but must not independently invent the underlying risk level.

Reviewer focus should similarly be derived from the files and modules actually changed.

---

## Testing Information

The initial pull request feature will not execute arbitrary repository test, lint, audit, or quality commands.

DiffSage must not claim that tests or quality checks passed unless those checks were actually executed and their results are available.

The initial implementation may include factual testing information derived from the branch, such as:

- Test files changed.
- Existing test-related changes.
- Indication that no checks were executed by DiffSage.

Execution of repository quality checks is intentionally deferred to a future feature.

A future implementation may introduce a dedicated `QualityGateService` and an opt-in workflow such as:

```bash
diffsage pr --run-checks
```

That feature will require explicit handling for tool discovery, command execution, output capture, exit codes, timeouts, missing tools, and normalized results.

---

## Service Architecture

Pull request generation will follow the existing layered architecture.

The primary service will be:

```text
PullRequestService
```

It will coordinate:

- Git context collection.
- Repository context.
- Deterministic analysis.
- Prompt generation.
- AI generation.
- Pull request draft creation.
- Pull request creation.

Hosting-specific functionality will be abstracted behind:

```text
GitHostingService
```

with an initial GitHub implementation such as:

```text
GitHubClient
```

The intended structure is:

```text
Pull Request Command
        │
        ▼
PullRequestService
        │
        ├── GitService
        ├── PromptService
        ├── AIService
        └── GitHostingService
                │
                ▼
            GitHubClient
```

The core pull request generation workflow must not depend directly on GitHub implementation details.

---

## GitHub Integration

The initial implementation will target GitHub.

GitHub-specific operations should be isolated behind the hosting abstraction.

The initial GitHub implementation should reuse the user's existing GitHub CLI authentication where practical rather than introducing a second authentication system or custom OAuth implementation.

The first implementation may use the GitHub CLI (`gh`) for authenticated GitHub operations.

Direct GitHub API integration may be introduced later if the required workflow capabilities exceed what the GitHub CLI can provide.

---

## Credential Architecture

DiffSage already provides a credential management abstraction for AI provider credentials.

GitHub credentials should not introduce an unrelated credential storage mechanism.

Where credential storage is required for hosting integrations, the existing credential abstraction should be generalized to support non-AI credentials without coupling hosting credentials to the AI-provider model.

The credential architecture should continue to maintain:

- Credential separation from application configuration.
- Masked credential display.
- No credential exposure in logs.
- Explicit credential ownership and resolution.

Any expansion of the credential abstraction should be documented separately if it represents a significant architectural change.

---

## Pull Request Lifecycle

The initial command should provide a human-controlled workflow.

```text
diffsage pr
      │
      ▼
Analyze branch
      │
      ▼
Generate pull request draft
      │
      ▼
Preview
      │
      ├── [Y] Create
      ├── [E] Edit
      ├── [R] Regenerate
      └── [N] Cancel
      │
      ▼
GitHub Pull Request
```

The system must not automatically create a pull request without explicit user confirmation.

If a pull request already exists for the current branch, DiffSage must detect that condition rather than blindly creating a duplicate.

The initial implementation may limit existing-PR handling to detection and informational reporting. Updating existing pull requests is deferred.

---

## Alternatives Considered

### Generate Only a Pull Request Description

**Rejected.**

Generating only a title and body does not provide sufficient differentiation from existing GitHub and IDE tooling.

DiffSage will instead combine Git analysis, deterministic signals, structured AI generation, and optional hosting automation.

### Use Only the Latest Commit Message

**Rejected.**

A pull request represents the complete branch change rather than a single commit.

DiffSage will analyze the entire branch relative to the selected base branch.

### Let the AI Determine Repository Facts

**Rejected.**

The language model may hallucinate repository state, branch relationships, risk, or testing results.

Repository facts must come from Git and deterministic analysis.

### Execute All Repository Tests Automatically

**Deferred.**

Executing arbitrary repository commands introduces significant complexity around:

- Tool discovery.
- Cross-platform behavior.
- Execution time.
- Timeouts.
- Missing dependencies.
- Output parsing.
- Security considerations.

This will be considered later as a separate quality-gate capability.

### Direct GitHub API Integration

**Deferred for the initial implementation.**

The first implementation may use the GitHub CLI to reuse existing GitHub authentication and reduce initial authentication complexity.

A direct GitHub API implementation may be introduced later behind the same hosting abstraction.

### GitHub-Specific Pull Request Logic in Commands

**Rejected.**

Hosting-specific logic inside commands would couple the application to GitHub and make future GitLab or Bitbucket support more difficult.

Hosting functionality will remain behind the `GitHostingService` abstraction.

---

## Consequences

### Positive

- Pull request generation remains grounded in Git repository state.
- AI output is more useful because it is based on complete branch context.
- Risk and reviewer-focus information can be explained from deterministic evidence.
- Pull request generation remains independent of GitHub-specific details.
- The workflow is consistent with the existing `diffsage commit` experience.
- Human confirmation remains part of the creation workflow.
- The architecture can support additional hosting platforms later.
- Quality-gate execution can be added independently in the future.

### Negative

- Pull request generation is more complex than generating a simple description.
- Additional Git analysis and hosting abstractions are required.
- Base branch and existing-PR handling introduce additional edge cases.
- GitHub CLI becomes an initial runtime dependency for GitHub PR creation.
- Structured PR models introduce additional domain objects.

---

## Out of Scope

The following are explicitly outside the initial implementation:

- Automatic execution of arbitrary tests or linters.
- CI/CD orchestration.
- Automatic reviewer assignment.
- Automatic label inference.
- Milestone management.
- Issue management or automatic issue linking.
- Updating existing pull requests.
- Automatic merge operations.
- Merge conflict resolution.
- Multi-host support.
- Custom GitHub OAuth implementation.
- Fully automated pull request creation without user confirmation.

---

## Future Extensions

Potential future extensions include:

- `QualityGateService` for opt-in repository checks.
- CI status integration.
- Updating existing pull requests.
- Reviewer suggestions.
- Label suggestions.
- Issue linking.
- Direct GitHub API integration.
- GitLab and Bitbucket support.
- Merge assistance.
- Additional repository-aware PR analysis.

---

## Implementation Guidance

The implementation should follow the existing DiffSage conventions:

- Commands remain thin orchestration and presentation boundaries.
- Services contain business logic.
- Git operations remain behind Git abstractions.
- Provider-specific AI behavior remains behind provider abstractions.
- Views handle terminal presentation.
- Domain models carry structured data between layers.
- Known domain errors use project-specific exception types.
- Tests should cover service behavior, deterministic analysis, and command-level workflows.

The implementation should avoid coupling PR generation to a particular AI provider or Git hosting platform.

---

## References

- `docs/architecture.md`
- `docs/conventions.md`
- ADR-007: Provider Abstraction
- ADR-008: Provider Response Normalization
- ADR-010: Hierarchical Configuration Management