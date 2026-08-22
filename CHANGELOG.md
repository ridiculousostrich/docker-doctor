# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [2.1.0] - 2026-08-22

### Added

- HTTP Basic Authentication for the web dashboard (config-driven, env var overrides)
- Dashboard auth config section in `config.example.yaml`
- `flask-httpauth` dependency for secure credential verification
- `/api/health` endpoint exempt from auth for monitoring/health checks

### Changed

- Dockerfile: removed duplicate `backend/api/requirements.txt` copy/install (reduced build time and image layers)
- Dockerfile: changed `ARG AI_PROVIDER` default from `openai` to `ollama` to match actual usage
- `docker-compose.yml`: switched from direct Docker socket mount to `docker-socket-proxy` for improved security
- `docker-compose.yml`: removed orphan port 8585 (only 8586 is used)
- `docker-compose.yml`: changed config path from `/opt/docker-doctor/config.yaml` to `./config.yaml` for portability
- `docker-compose.yml`: placed services on an internal network with socket-proxy
- `README.md`: updated all version references to v2.1, improved compose examples
- `build-docker-image.sh`: updated to v2.1 with proper build args and `latest` tag

## [1.0.0] - 2026-08-01

### Added

- Full project documentation: `README.md`, `DEPLOYMENT.md`, `config.schema.json`, `LICENSE`
- Comprehensive test suite across all core components (`tests/` directory)
- Systemd service file and automated install script (`install.sh`)
- Prometheus `/metrics` endpoint for monitoring metrics
- HTML health history dashboard using Chart.js
- Automatic SQLite daily backups with retention
- Container image update notifications via Discord
- Configurable container monitoring via `containers` list in `config.yaml`
- REST API endpoints for querying monitoring data
- Exponential backoff retry logic for AI calls and Discord notifications
- GitHub Actions CI/CD pipeline for automated builds and tests
- Multi-provider AI support (Ollama, OpenAI, Anthropic)
- Versioning policy (SemVer) and release branching strategy

### Changed

- Modular architecture with clear component separation
- Config validation using `config.schema.json`
- Daily report generation with health indicators (🟢🟡🔴)
- Trend analysis comparing today's data with yesterday's metrics

### Fixed

- Noise filtering in log collection (e.g., "context canceled" messages)
- Error classification into categories (network, authentication, storage, etc.)
- Graceful shutdown handling and timeout management

### Removed

- None

[2.1.0]: https://github.com/ridiculousostrich/docker-doctor/compare/v1.0.0...v2.1.0
[1.0.0]: https://github.com/ridiculousostrich/docker-doctor/compare/v1.0.0...HEAD
