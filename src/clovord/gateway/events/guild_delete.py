from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.guild import Guild

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GUILD_DELETE"
INTERNAL_EVENT_NAME = "on_guild_delete"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    guild: Guild | Any = data_part
    if isinstance(data_part, dict):
        guild_id = str(data_part.get("id") or data_part.get("guild_id") or "")
        removed = bot._remove_guild(guild_id) if guild_id else None
        guild = removed or Guild.from_dict(data_part, bot=bot)

    await bot.events.dispatch(INTERNAL_EVENT_NAME, guild)
