# Changelog

All notable changes to Reconnator are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Provider-agnostic agent runtime with local presets for Ollama, vLLM, LM Studio,
  and llama.cpp, using Qwen through Ollama by default.
- Runtime policy enforcement for MCP tool allowlists, operator approval, and
  authorized target scope.
- Telegram commands for granting, inspecting, and revoking per-chat scan scope.
- Local-model configuration for Docker and Helm deployments.
- Agent-core unit tests and a dedicated GitHub Actions test workflow.

### Changed

- Gemini is now an optional compatibility provider instead of a mandatory runtime
  dependency.
- Telegram requests are restricted to configured operator chat IDs.

## [2.0.1] - 2026-08-28

### Added

- GitHub Container Registry publishing for the main Reconnator image.
- Security policy, contribution guidelines, Contributor Covenant, issue forms,
  and a pull request template.
- GitHub Sponsors configuration and project sponsorship guidance.
- Public project Wiki covering setup, architecture, configuration, deployment,
  integrations, security, troubleshooting, development, and frequently asked
  questions.
- Choice-based dual licensing under `MIT OR Apache-2.0`.
- A repository-hosted README banner.
- Semantic Versioning release documentation, generated release-note
  configuration, and Dependabot configuration.

### Fixed

- Restored the Docker image pipeline by configuring Docker Buildx before using
  the GitHub Actions cache exporter.
- Updated Docker-related GitHub Actions to current major versions.
- Corrected PDF report generation and normalized scanner results passed into
  reports.

### Changed

- Container publishing now produces SemVer tags (`2.0.1`, `2.0`, and `2`) when
  a stable `vMAJOR.MINOR.PATCH` Git tag is pushed.
- Improved project documentation, script descriptions, and responsible-use
  guidance.

## [2.0.0] - 2026-07-31

### Added

- Gemini-powered conversational orchestration through the Model Context
  Protocol (MCP).
- Telegram ChatOps operation as a continuously running bot.
- Ephemeral Nmap, Ffuf, Nuclei, Subfinder, and dnsx scanner workers.
- Automated PDF report generation with ReportLab.
- Docker and Helm deployment resources for the v2 architecture.

### Changed

- Replaced the scheduled passive-reconnaissance flow with an interactive,
  container-native reconnaissance architecture.

[Unreleased]: https://github.com/amiencoy/Reconnator/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/amiencoy/Reconnator/releases/tag/v2.0.1
[2.0.0]: https://github.com/amiencoy/Reconnator/commit/9899c7f
