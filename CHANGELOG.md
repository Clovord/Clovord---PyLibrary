# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.1.20] - 2026-08-23
### Added
- Send `api_version` in gateway Identify and log backend build info from READY `api` payload.

## [0.1.17] - 2026-08-17
### Changed
- Default REST base URL is now `https://clovord.com/api/v2`.

## [0.1.13] - 2026-07-01
### Fixed
- update version to 0.1.13 in pyproject.toml

### Docs
- update for v0.1.13dev4

## [0.1.13dev4] - 2026-07-01
### Fixed
- update version to 0.1.13dev4 in pyproject.toml and enhance message handling in message\_create.py

### Docs
- update for v0.1.13dev2

### Other
- Merge branch 'main' of https://github.com/Clovord/Library---py---clovord.py

## [0.1.13dev2] - 2026-07-01
### Added
- implement Channel model and enhance message handling with user context

## [0.1.12dev5] - 2026-07-01
### Added
- add support for extension modules and enhance error handling

### Fixed
- remove unused on\_ready\_payload event handler from README
- revert version to 0.1.12 from 0.1.12dev4

### Docs
- update for v0.1.12dev4

### Other
- Merge branch 'main' of https://github.com/Clovord/Library---py---clovord.py

## [0.1.12dev4] - 2026-06-12
### Added
- update version to 0.1.12dev4 and enhance logger setup

### Docs
- update for v0.1.12dev3

### Other
- Merge branch 'main' of https://github.com/Clovord/Library---py---clovord.py

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
