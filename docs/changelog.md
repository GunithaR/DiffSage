# Changelog

## [1.2.1] - 2026-08-13

### Fixed

- Added user-friendly handling for unavailable AI models in the `ask` command.
- Prevented model-not-found errors from being reported as unexpected errors.
- Added command-level test coverage for model-not-found error handling.


## [1.2.0] - 2026-08-12

### Added
- Hierarchical configuration resolution (environment, global, and local configuration).
- `diffsage config list` command to display the active configuration.
- `diffsage config get` command to retrieve individual configuration values.
- BaseView abstraction for shared terminal UI behavior.
- Configuration report models and supporting services.
- Provider credential management through `diffsage auth` commands.
- Named credential profiles for provider authentication.
- Dedicated credential storage separate from application configuration.
- Credential resolution through `CredentialService`.
- Credential-specific error handling for missing provider credentials.
- Integration between credential management and AI provider creation.
- Gemini provider authentication using resolved credentials.
- Comprehensive unit and integration tests for credential management and AI integration.

### Changed
- Refactored terminal views to inherit from `BaseView`.
- Improved configuration command error handling with user-friendly messages.
- Normalized configuration key lookups to be case-insensitive.
- Removed direct API-key resolution from application settings and environment variables.
- Updated `AIService` to resolve provider credentials before creating AI providers.
- Updated provider factory and provider implementations to receive resolved credentials.
- Improved Gemini provider error handling with user-friendly authentication and provider errors.
- Updated `ask` and `commit` commands to use the credential management system.
- Updated Typer to 0.27.x and Click to 8.3.3+ after verifying compatibility with required CLI argument validation.

### Fixed
- Resolved a Typer and Click compatibility issue that caused missing required CLI arguments to be passed as `None` instead of triggering normal argument validation.
- Prevented raw Gemini authentication errors from being exposed directly to users.
- Added explicit handling for missing provider credentials.


## [1.1.0] - 2026-07-30

### Added
- AI-assisted Git commit workflow.
- Interactive commit preview with confirmation, editing, regeneration, and cancellation.
- Rich terminal UI for commit generation.
- Dedicated commit parser and typed commit message model.
- Expanded automated test coverage.

### Changed
- Improved application architecture through dedicated parsers, views, models, and services.
- Centralized exception handling and consistent logging.
- Enhanced terminal output and user interaction flow.

### Fixed
- Improved reliability and terminal output management.


## [1.0.1] - 2026-07-26

### Added
- README
- vision.md
- ADR-009
- MIT License

### Changed
- Project positioning updated to AI-aware Git workflow toolkit.
- Version bumped to 1.0.1.

### Fixed
- Documentation consistency.