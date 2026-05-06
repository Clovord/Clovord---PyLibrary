from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "READY"
INTERNAL_EVENT_NAME = "on_ready"

async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    username, user_id = _extract_ready_identity(data_part)
    bot._logger.info("Connected to gateway as %s (%s)", username, user_id)

    if bot._auto_online_presence and not bot._presence_set_explicitly:
        try:
            await bot.gateway.update_presence("online", _from_ready=True)
        except Exception as exc:
            bot._logger.warning("Failed to set online presence: %s", exc)

    await bot.events.dispatch(INTERNAL_EVENT_NAME)


def _extract_ready_identity(data: Any) -> tuple[str, str]:
    if not isinstance(data, dict):
        return "unknown", "unknown"

    candidates: list[dict[str, Any]] = []
    for key in ("user", "me", "bot", "client"):
        value = data.get(key)
        if isinstance(value, dict):
            candidates.append(value)

    # Fallback: some payloads may keep identity fields at READY root.
    candidates.append(data)

    for item in candidates:
        user_id = item.get("id")
        username = item.get("username") or item.get("name") or item.get("display_name")
        if user_id is None and username is None:
            continue

        normalized_username = str(username) if username is not None else "unknown"
        normalized_user_id = str(user_id) if user_id is not None else "unknown"
        return normalized_username, normalized_user_id

    return "unknown", "unknown"
