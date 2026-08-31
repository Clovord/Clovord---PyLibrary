from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "REIDENTIFIED"
INTERNAL_EVENT_NAME = "on_reidentified"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if isinstance(data_part, dict):
        guild_ids = [str(item) for item in (data_part.get("guild_ids") or []) if str(item).strip()]
        if guild_ids:
            bot._set_guild_ids(guild_ids)

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
