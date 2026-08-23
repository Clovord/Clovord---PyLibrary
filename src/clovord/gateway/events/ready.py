from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.user import User
from ...utils.library_update_check import check_and_notify_library_update

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "READY"
INTERNAL_EVENT_NAME = "on_ready"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    user = _extract_ready_user(data_part)
    if user is not None:
        bot._user = user

    username = bot.user.username if bot.user is not None else "unknown"
    user_id = bot.user.id if bot.user is not None else "unknown"
    bot._logger.info("Connected to gateway as %s (%s)", username, user_id)
    _log_ready_intents(bot, data_part)
    _log_api_info(bot, data_part)

    if bot._auto_online_presence and not bot._presence_set_explicitly:
        try:
            await bot.gateway.update_presence("online", _from_ready=True)
        except Exception as exc:
            bot._logger.warning("Failed to set online presence: %s", exc)

    await check_and_notify_library_update(bot)
    await bot.events.dispatch(INTERNAL_EVENT_NAME)


def _log_api_info(bot: Bot, data: Any) -> None:
    if not isinstance(data, dict):
        return

    api = data.get("api")
    if not isinstance(api, dict):
        return

    client_version = api.get("version") or "unknown"
    build = api.get("build") if isinstance(api.get("build"), dict) else {}
    build_id = build.get("build_id", "N/A")
    commit = build.get("commit") or "N/A"
    channel = build.get("channel") or "N/A"
    supported = api.get("supported_versions")
    supported_text = ", ".join(str(item) for item in supported) if isinstance(supported, list) else "N/A"

    log_message = (
        "=== CLOVORD API INFO ===\n"
        f"REST API Version: {client_version}\n"
        f"Supported Versions: {supported_text}\n"
        f"Backend Build ID: {build_id}\n"
        f"Commit: {commit}\n"
        f"Channel: {channel}\n"
        "========================"
    )
    bot._logger.info(log_message)


def _log_ready_intents(bot: Bot, data: Any) -> None:
    intents = data.get("intents") if isinstance(data, dict) else None
    if not isinstance(intents, dict):
        return

    requested = _normalize_intent_names(intents.get("requested"))
    granted = _normalize_granted_intents(intents.get("granted"))
    denied = _normalize_intent_names(intents.get("denied"))
    invalid = _normalize_intent_names(intents.get("invalid"))

    if granted:
        granted_text = ", ".join(
            f"{name} ({level})" if level else name for name, level in granted
        )
        bot._logger.info("Granted gateway intents: %s", granted_text)

    for intent_name in denied:
        bot._logger.error(
            "Intent not permitted: %s. This application is not allowed to use that intent, "
            "so events that require it will not be received.",
            intent_name,
        )

    for intent_name in invalid:
        bot._logger.warning(
            "Unknown intent requested and ignored by the gateway: %s",
            intent_name,
        )

    if requested and not granted and not denied and not invalid:
        bot._logger.info("Requested gateway intents: %s", ", ".join(requested))


def _normalize_intent_names(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value if str(key).strip()]
    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                names.append(text)
        return names
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_granted_intents(value: Any) -> list[tuple[str, str | None]]:
    if isinstance(value, dict):
        granted: list[tuple[str, str | None]] = []
        for key, level in value.items():
            name = str(key).strip()
            if not name:
                continue
            level_text = str(level).strip() if level is not None else ""
            granted.append((name, level_text or None))
        return granted

    return [(name, None) for name in _normalize_intent_names(value)]


def _extract_ready_user(data: Any) -> User | None:
    if not isinstance(data, dict):
        return None

    candidates: list[dict[str, Any]] = []
    for key in ("user", "me", "bot", "client"):
        value = data.get(key)
        if isinstance(value, dict):
            candidates.append(value)

    # Fallback: some payloads may keep identity fields at READY root.
    candidates.append(data)

    for item in candidates:
        if item.get("id") is None and item.get("username") is None and item.get("name") is None and item.get("display_name") is None:
            continue

        payload = {
            "id": item.get("id", "unknown"),
            "username": item.get("username") or item.get("name") or item.get("display_name") or "unknown",
        }
        return User.from_dict(payload)

    return None
