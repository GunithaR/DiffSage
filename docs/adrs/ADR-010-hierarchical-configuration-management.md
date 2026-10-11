# ADR-010: Hierarchical Configuration Management

- **Status:** Accepted
- **Date:** 2026-07-30

---

# Context

DiffSage initially relied primarily on environment variables to configure AI providers, models, and application settings. Provider authentication was subsequently separated into a dedicated credential management system.

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
Configuration resolution (current + planned)
    CLI overrides
        ↓
    Environment variables
        ↓
    Local .diffsage.toml
        ↓
    Global configuration
        ↓
    Application defaults


Authentication
    CredentialService
        ↓
    CredentialsRepository
        ↓
    credentials.toml
        ↓
    Provider
```

The initial implementation introduces application defaults, global configuration,
repository-local configuration, and environment variable overrides.

Configuration values are resolved by merging each layer in precedence order,
allowing later sources to override earlier ones while preserving unspecified defaults.

Authentication credentials remain intentionally outside the configuration system.

Command-line configuration overrides remain a future extension.

Each successive layer overrides the layers beneath it.

This approach provides sensible defaults for everyday development while allowing temporary overrides for automation and project-specific customization.

---

# Global Configuration

DiffSage will maintain a user-level configuration file containing the developer's preferred defaults.

Typical settings include:

- Default AI provider
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
[ai]
provider = "gemini"
model = "gemini-3.5-flash-lite"
max_output_tokens = 1000

[network]
timeout = 60
max_retries = 3

[logging]
level = "INFO"
```

---

# Configuration Storage Strategy

Configuration files store only values explicitly overridden by the user.

All unspecified values are inherited from the application defaults during
configuration resolution.

For example, a repository configuration may contain only:

```toml
[network]
timeout = 120
```

---

# Configuration Philosophy

DiffSage intentionally separates user configuration from authentication.

User preferences are stored in configuration files, while secrets are stored separately.

Configuration includes:

- AI provider
- AI model
- Request timeout
- Retry policy
- Logging level

Authentication uses:

- DiffSage credential profiles
- credentials.toml
- CredentialService
- CredentialsRepository

This separation prevents configuration files from containing secrets while
allowing configuration to be shared safely.

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

DiffSage currently provides direct configuration commands for inspecting,
updating, and removing configuration values.

Examples:

```bash
diffsage config list
diffsage config get provider
diffsage config set provider gemini
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

The credential management system:

- Avoids printing full credentials in terminal output.
- Masks API keys when credentials are displayed.
- Keeps provider credentials outside the application configuration model.
- Avoids exposing credentials through diagnostic output.

Where supported, credentials may eventually be stored using operating-system facilities such as:

- macOS Keychain
- Windows Credential Manager
- Linux Secret Service

Environment variables remain fully supported for CI/CD pipelines and automated environments.

---

## Authentication Architecture

Configuration and authentication are intentionally treated as separate concerns.

Configuration defines how DiffSage should behave, while authentication manages access to external AI providers.

DiffSage provides dedicated authentication commands for managing provider credentials.

Examples:

```bash
diffsage auth set gemini              # prompts for the key with hidden input
diffsage auth set gemini --name paid

diffsage auth get gemini
diffsage auth list
diffsage auth unset gemini
```

API keys are never accepted as command-line arguments, which would leave them in shell
history and visible to other processes. `auth set` reads the key from a hidden prompt, or
from standard input when it is piped (for scripts).

Authentication commands allow users to create, retrieve, list, and remove
provider credential profiles while keeping API keys separate from application
configuration.

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

Existing environment-variable-based configuration workflows remain supported. Provider API keys are no longer resolved from DIFFSAGE_API_KEY; provider credentials are managed through DiffSage’s credential management system.

The hierarchical configuration system extends the existing behavior rather than replacing it.

Users may continue using environment variables for application configuration
and CI/CD overrides. Provider credentials are managed separately through the
credential management system.

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

The configuration architecture has been implemented in the following areas:

1. Introduced a configuration abstraction capable of resolving multiple configuration sources.
2. Integrated `platformdirs` for platform-native configuration storage.
3. Added global configuration loading.
4. Added repository-level `.diffsage.toml` configuration.
5. Implemented hierarchical configuration resolution using environment variables,
   local repository configuration, global configuration, and application defaults.
6. Introduced configuration repository abstractions.
7. Introduced configuration service validation and normalization.
8. Introduced configuration report models.
9. Added `diffsage config` commands.
10. Added automated configuration tests.
11. Separated provider authentication from application configuration through a dedicated credential store and `diffsage auth` commands.

The following areas remain future work:

12. Add command-line configuration overrides with per-invocation precedence.
13. Add an interactive `diffsage init` configuration wizard.
14. Continue evolving documentation and installation guides as the configuration system develops.

---

# References

- `docs/architecture.md`
- `docs/conventions.md`
- ADR-009: Project Positioning
- `pyproject.toml`
