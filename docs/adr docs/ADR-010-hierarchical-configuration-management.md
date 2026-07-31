# ADR-010: Hierarchical Configuration Management

- **Status:** Proposed
- **Date:** 2026-07-30

---

# Context

DiffSage currently relies primarily on environment variables (optionally loaded from a `.env` file) to configure AI providers, models, API credentials, and application settings.

While this approach works well during development, it presents several limitations as DiffSage evolves into a globally installable command-line application.

Users installing DiffSage through package managers such as `pipx` should not be required to manually create `.env` files or permanently export environment variables in their shell before using the application.

Additionally, future releases will introduce:

- Global installation via PyPI
- Cross-platform support
- Project-specific configuration
- CI/CD automation
- Multiple AI providers
- Additional configurable features

These requirements demand a more flexible and maintainable configuration architecture.

The project therefore requires a hierarchical configuration system capable of supporting different execution environments while maintaining a predictable resolution strategy.

---

# Decision

DiffSage will adopt a hierarchical configuration system with multiple configuration sources.

Configuration values will ultimately be resolved according to the following precedence order (highest priority first):

```
Command Line Arguments
        │
        ▼
Environment Variables
        │
        ▼
Credential Store
        │
        ▼
Local Repository Configuration
(.diffsage.toml)
        │
        ▼
Global User Configuration
        │
        ▼
Application Defaults
```

The initial implementation introduces the hierarchy up to environment variables.

Credential storage and command-line overrides will be introduced in future iterations while preserving this resolution order.

Each successive layer overrides the layers beneath it.

This approach provides sensible defaults for everyday development while allowing temporary overrides for automation and project-specific customization.

---

# Global Configuration

DiffSage will maintain a user-level configuration file containing the developer's preferred defaults.

Typical settings include:

- Default AI provider
- Default provider profile
- Default model
- Request timeout
- Retry policy
- Logging preferences
- Output preferences

Global configuration intentionally excludes API credentials.

---

# Local Repository Configuration

Repositories may optionally contain a project-specific configuration file.

```
.diffsage.toml
```

This configuration is intended for repository-level settings that should be shared among contributors.

Examples include:

- Preferred provider
- Preferred model
- Prompt behavior
- Repository-specific defaults

Local configuration overrides the global configuration but may itself be overridden by environment variables.

Repository configuration should contain only repository-specific behavior.

Examples include:

- Preferred provider
- Preferred provider profile
- Preferred model
- Prompt behaviour
- Repository defaults

Repository configuration must not store authentication credentials.

---

# Environment Variables

Environment variables remain fully supported.

They provide the preferred mechanism for:

- CI/CD pipelines
- Temporary overrides
- Automated workflows
- Containerized environments

Environment variables override both global and repository configuration.

This preserves compatibility with existing workflows while enabling modern deployment practices.

---

# Command Line Configuration

Future command-line options may override all other configuration sources for a single invocation.

Examples include:

```bash
diffsage commit --provider openai

diffsage commit --model gpt-5.5
```

These values apply only to the current execution and are not persisted.

---

# Configuration Storage

DiffSage will use the `platformdirs` library to determine operating system specific configuration directories.

Typical locations include:

Linux

```
~/.config/DiffSage/
```

macOS

```
~/Library/Application Support/DiffSage/
```

Windows

```
%LOCALAPPDATA%\DiffSage\
```

The project intentionally avoids hardcoded paths such as:

```
~/.diffsage
```

to ensure platform-native behavior.

---

# Configuration Format

Configuration files will use the TOML format.

Example:

```toml
provider = "gemini"
model = "gemini-2.5-flash"

timeout = 60
max_retries = 3

[logging]
level = "INFO"
```

---

# Rationale

TOML was selected because it:

- Is the standard configuration format within the Python ecosystem.
- Is already familiar to contributors through `pyproject.toml`.
- Supports structured configuration.
- Is human-readable.
- Supports comments.
- Avoids unnecessary complexity.

Alternative formats such as JSON and YAML were considered but not selected.

---

# Interactive Configuration

Future configuration commands will support both direct and interactive editing.

Examples:

```bash
diffsage config list

diffsage config get provider

diffsage config set provider gemini

diffsage config set profile work

diffsage config set model gemini-2.5-flash

diffsage config unset provider
```

Interactive configuration may also be provided for improved usability.

Example:

```bash
diffsage config
```

or

```bash
diffsage init
```

The interactive experience should guide users through selecting providers, models, and preferred defaults without requiring manual editing of configuration files.

---

## Security Considerations

Authentication credentials are intentionally separated from configuration.

Configuration files should never contain API keys.

The initial implementation will:

- Restrict file permissions where supported.
- Avoid printing credentials in terminal output.
- Avoid exposing secrets through diagnostic commands.

Future versions will introduce a dedicated credential store managed through `diffsage auth`.

Where supported, credentials may eventually be stored using operating-system facilities such as:

- macOS Keychain
- Windows Credential Manager
- Linux Secret Service

Environment variables remain fully supported for CI/CD pipelines and automated environments.

---

## Authentication Architecture

Configuration and authentication are intentionally treated as separate concerns.

Configuration defines how DiffSage should behave, while authentication manages access to external AI providers.

Future versions of DiffSage will introduce dedicated authentication commands.

Examples:

```bash
diffsage auth login

diffsage auth list

diffsage auth remove
```

Authentication commands will guide users through selecting an AI provider, creating a profile, and securely storing credentials.

Configuration files will reference providers and profiles rather than storing API keys directly.

Example conceptual model:

Gemini
├── personal
├── work
└── university

Anthropic
├── work
└── enterprise

This separation allows multiple accounts for the same provider while keeping credentials independent from user configuration.

---

# Backward Compatibility

Existing environment-variable-based workflows will continue to function without modification.

The hierarchical configuration system extends the existing behavior rather than replacing it.

Users who prefer environment variables may continue using them exclusively.

---

# Future Configuration Model

The intended separation of responsibilities is:

| Component | Responsibility |
|-----------|----------------|
| Application Defaults | Internal DiffSage defaults |
| Global Configuration | User preferences |
| Local Configuration | Repository-specific behaviour |
| Credential Store | Provider credentials and authentication |
| Environment Variables | Temporary or CI/CD overrides |
| Command Line Arguments | One-time command overrides |

This separation allows DiffSage to evolve without coupling user preferences, repository configuration, and authentication.

---

# Consequences

## Positive

- Improved first-time user experience.
- Platform-native configuration storage.
- Better separation between user and project configuration.
- Flexible configuration overrides.
- Improved compatibility with package distribution.
- Cleaner CI/CD integration.
- Scalable foundation for future configuration options.

## Negative

- Increased implementation complexity.
- Multiple configuration sources require deterministic resolution logic.
- Additional testing required across operating systems.

---

# Alternatives Considered

## Continue Using Environment Variables Only

Rejected.

Although simple, this approach creates unnecessary friction for globally installed applications and does not support repository-specific defaults.

---

## Single Global Configuration File

Rejected.

A global-only configuration cannot express project-specific behavior shared by repository contributors.

---

## JSON Configuration

Rejected.

JSON lacks comments and is less suitable for manually edited configuration files.

---

## YAML Configuration

Rejected.

Although flexible, YAML introduces additional complexity that is unnecessary for DiffSage's configuration requirements.

---

## Hierarchical TOML Configuration (Selected)

This approach balances usability, flexibility, platform compatibility, and long-term maintainability while aligning with conventions used by modern developer tools.

---

# Implementation Notes

Implementation should proceed in the following order:

1. Introduce a configuration abstraction capable of resolving multiple configuration sources.
2. Integrate `platformdirs` for platform-native configuration storage.
3. Support global configuration loading.
4. Support repository-level `.diffsage.toml`.
5. Merge configuration according to the defined precedence order.
6. Add `diffsage config` commands.
7. Add an interactive `diffsage init` wizard.
8. Update documentation and installation guides.

---

# References

- `docs/architecture.md`
- `docs/conventions.md`
- ADR-009: Project Positioning
- `pyproject.toml`
