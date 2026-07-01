from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.user import User

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

    if bot._auto_online_presence and not bot._presence_set_explicitly:
        try:
            await bot.gateway.update_presence("online", _from_ready=True)
        except Exception as exc:
            bot._logger.warning("Failed to set online presence: %s", exc)

    await bot.events.dispatch(INTERNAL_EVENT_NAME)


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
