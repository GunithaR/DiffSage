# Changelog

## [Unreleased]

### Added

- Shared command error handler: every DiffSage error is shown as one `✗` message with a consistent exit code; unexpected errors are logged with a traceback.
- Global error handler with logic to allow specific commands to run even when the configuration is invalid.
- Application of the error handling decorator to the `auth` command and simplified credential service initialization.
- `diffsage doctor` reports an invalid configuration instead of crashing.
- End-to-end test harness: isolated config and logs, a fake AI provider, a fake GitHub CLI, and real temporary Git repositories with an origin remote.
- End-to-end tests for the `commit` and `pr` workflows through the real CLI.
- Strict expected-failure tests for known bugs, to be converted into regression tests as each bug is fixed.
- mypy type checking in CI, with a temporary baseline for modules with known type errors.

### Changed

- CI runs the test suite on Ubuntu, macOS and Windows.
- The release workflow verifies that the tag matches the package version and runs lint and tests before building and publishing.
- Ruff now reports unused arguments.

### Fixed

- Rate-limit and other provider errors in `ask`, unparseable AI commit messages, editor launch failures and `gh pr create` failures were reported as "unexpected error".
- An invalid configuration file crashed every command with a traceback; it is now reported with the file, setting and value at fault.
- `config set` and `config unset` can repair a broken configuration file, and `config list`/`get --global`/`--local` can still read it.
- Dependabot configuration was invalid; it now also updates GitHub Actions.
- Redundant try-except blocks across CLI commands removed in favor of the centralized error handling decorator.


## [1.3.1] - 2026-08-23

### Added

- Added `diffsage --version` and `diffsage -v` options to display the installed DiffSage version.
- Added automated tests for the version options.

### Changed

- CLI version information is resolved from the installed package metadata.


## [1.3.0] - 2026-08-23

### Added

- AI-assisted pull request generation from Git repository evidence.
- Interactive pull request draft review workflow.
- Pull request draft editing and regeneration.
- Structured pull request draft parsing and validation.
- GitHub CLI integration for pull request creation.
- GitHub CLI availability and authentication validation.
- Remote branch synchronization validation before pull request creation.
- Pull request creation through GitHub.
- Pull request URL display after successful creation.
- Comprehensive automated tests for pull request generation and creation.
- Display AI generation attempt progress during commit message generation.
- Display AI generation attempt progress during pull request draft generation.

### Changed

- Improved CLI feedback during AI provider retries by displaying the current generation attempt and total allowed attempts.


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