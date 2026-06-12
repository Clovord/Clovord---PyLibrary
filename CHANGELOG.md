# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.1.12dev3] - 2026-06-12
### Fixed
- update version to 0.1.12dev3 and adjust import paths in event handlers

### Docs
- update for v0.1.12dev2

## [0.1.12dev2] - 2026-06-12
### Added
- update version to 0.1.12dev2
- implement library update event handling with logging
- add webhook notification for clovord.py release process

### Docs
- update for v0.1.12dev1

## [0.1.12dev1] - 2026-05-19
### Added
- add DOMAINLIST\_ENTRY\_CREATE event handling
- update version to 0.1.11, enhance event error handling, and improve HTTP client retry logic

### Fixed
- update version to 0.1.10 and add gateway shutdown event handling

### Docs
- update for v0.1.10
- update for v0.1.10dev9

## [0.1.10] - 2026-05-05
### Fixed
- update version to 0.1.10 and add gateway shutdown event handling

### Docs
- update for v0.1.10dev9

## [0.1.10dev9] - 2026-05-03
### Changed
- update handle function signatures and improve payload handling across gateway events

### Docs
- update for v0.1.10dev8

## [0.1.10dev8] - 2026-05-03
### Fixed
- correct type casting for extracted user identity in handle function

### Docs
- update for v0.1.10dev7

## [0.1.10dev7] - 2026-05-03
### Fixed
- update version to 0.1.10dev7 and improve presence update handling

### Docs
- update for v0.1.10dev6

## [0.1.10dev6] - 2026-05-03
### Added
- add support for switching to default branch before committing changelog updates

### Fixed
- Fixed an issue with the Changelog generation from github

## [0.1.10dev2] - 2026-05-03
### Added
- update version to 0.1.10dev1 and add gateway error handling

## [0.1.3] - 2026-04-30
### Added
- Intents helper API with flag-style configuration.
- Gateway identify payload aligned with API protocol.
- Improved gateway error reporting with full payload context.
- Optional ready payload event for debugging: on_ready_payload.
- Release automation via GitHub Actions trusted publishing workflow.

### Changed
- Package metadata and release documentation for public distribution.

## [0.1.0] - 2026-04-30
### Added
- Initial SDK structure with Bot, Gateway, HTTP client, models, and custom errors.
