from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.guild import Guild

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GUILD_CREATE"
INTERNAL_EVENT_NAME = "on_guild_create"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if isinstance(data_part, dict):
        guild = Guild.from_dict(data_part, bot=bot)
        bot._cache_guild(guild)
        await bot.events.dispatch(INTERNAL_EVENT_NAME, guild)
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
