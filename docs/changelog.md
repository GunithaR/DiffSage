# Changelog

## [Unreleased]

### Added
- Hierarchical configuration resolution (environment, global, and local configuration).
- `diffsage config list` command to display the active configuration.
- `diffsage config get` command to retrieve individual configuration values.
- BaseView abstraction for shared terminal UI behavior.
- Configuration report models and supporting services.
- Comprehensive unit tests for configuration resolution and CLI commands.

### Changed
- Refactored terminal views to inherit from `BaseView`.
- Improved configuration command error handling with user-friendly messages.
- Normalized configuration key lookups to be case-insensitive.

### Fixed
- Pinned Click to the 8.1.x release line due to a compatibility issue with Typer 0.16.x that caused missing required CLI arguments to be passed as `None`.


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