# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.1.36] - 2026-09-06

### Changed
- Guild ban/unban paths no longer include `/settings` (`/guilds/{id}/bans`).

## [0.1.35] - 2026-09-06

### Added
- `Guild.unban()` for `DELETE /guilds/{guild_id}/bans/{user_id}`

## [0.1.34] - 2026-08-31
### Fixed
- Remove `reason` and `sources` from `DomainlistEntry`; bot API responses do not expose these fields.
- Document `DomainlistEntry.host` as an SDK helper that joins `subdomain` and `domain`.

### Docs
- Correct Phase 3 developer news for public domainlist fields.

## [0.1.33] - 2026-08-31
### Fixed
- Slash command dispatch now rejects interactions that are missing required handler parameters before invoking the callback.

## [0.1.32] - 2026-08-31
### Fixed
- Slash command handlers now auto-register options from function parameters and receive bound values on dispatch.

## [0.1.31] - 2026-08-31
### Added
- Domainlist REST: `bot.search_domain()` and `bot.search_domains()` for `GET /domains/search`.
- `DomainlistEntry.from_search_response()` for multi-status API envelopes.
- Components V2 builders: `StringSelect`, `SelectOption`, `Section`, `Thumbnail`, `MediaGallery`, `MediaGalleryItem`, and `ButtonStyle`.

## [0.1.30] - 2026-08-31
### Changed
- `InteractionFollowup` now uses Clovord-native interaction endpoints instead of webhook URLs:
  - `POST /interactions/{id}/{token}/followup`
  - `PATCH /interactions/{id}/{token}/messages/@original`
  - `DELETE /interactions/{id}/{token}/messages/@original`

## [0.1.29] - 2026-08-31
### Fixed
- Error recovery after `defer()` now edits the deferred response instead of sending a second message.
- `Interaction` tracks whether it was deferred (`interaction._deferred`).

## [0.1.28] - 2026-08-31
### Fixed
- Slash command handlers that fail after `defer()` no longer leave interactions stuck on "Waiting for response…".
- `InteractionFollowup.send()` and `edit_original()` now set the Components V2 flag for layout components.

## [0.1.27] - 2026-08-31
### Added
- REST resource methods on models: `Channel.fetch/history/send`, `Message.edit/delete`, `Guild.fetch/fetch_channels/fetch_members/fetch_member/fetch_roles/create_role/kick/ban`, `Member.edit`, `Role.edit/delete`.
- `bot.fetch_channel()` for direct channel lookups.
- `InteractionFollowup` (`interaction.followup.send/edit_original/delete_original`) for slash-command follow-ups.
- `Webhook` helper for executing webhook URLs without bot auth headers.
- Shared `unwrap_payload()` helper and per-request bot auth control in `HTTPClient`.

## [0.1.26] - 2026-08-31
### Added
- Core bot lifecycle properties: `bot.is_ready`, `bot.started_at`, `bot.uptime`, `bot.guild_ids`, `bot.guilds`, and `bot.get_guild()`.
- Clovord-native models: `Guild`, `Member`, `Role`, `DomainlistEntry`, `Typing`, and `PartialMessage`.
- Expanded `User`, `Message`, and `Channel` models with additional API fields and `.raw` payload access.
- Gateway events: `MESSAGE_DELETE`, `CHANNEL_UPDATE`, `GUILD_CREATE`, `GUILD_UPDATE`, `GUILD_DELETE`, `GUILD_MEMBER_ADD`, `GUILD_MEMBER_UPDATE`, `GUILD_MEMBER_REMOVE`, and `REIDENTIFIED`.
- READY now caches guild objects and marks the bot as ready.
- Time helpers: `format_uptime()`, `format_timestamp()`, and `format_relative_timestamp()` for readable durations and `<t:unix:R>` markers.

## [0.1.25] - 2026-08-26
### Added
- `TYPING_START` gateway event (`on_typing_start`) and `Channel.trigger_typing()` for Discord-compatible typing indicators.

## [0.1.24] - 2026-08-26
### Changed
- Library logs always use a fixed `❱❱ CLV - {ISO-8601} - LEVEL ❱❱` prefix on every physical line (including multi-line notices and tracebacks) via a dedicated `clovord` logger (not the process root), so they stay distinguishable when bots run alongside other async logging.

## [0.1.21] - 2026-08-23
### Fixed
- Improve `LIBRARY_UPDATE` logging with current and new version, skip stale notices, and fix release webhook version metadata.

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
