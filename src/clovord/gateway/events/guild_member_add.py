from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.guild import Guild
from ...models.member import Member

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GUILD_MEMBER_ADD"
INTERNAL_EVENT_NAME = "on_guild_member_add"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if not isinstance(data_part, dict):
        await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
        return

    guild_payload = data_part.get("guild") if isinstance(data_part.get("guild"), dict) else None
    guild_id = str(guild_payload.get("id")) if guild_payload else str(data_part.get("guild_id") or "")
    member = Member.from_dict(
        data_part.get("member") if isinstance(data_part.get("member"), dict) else data_part,
        guild_id=guild_id or None,
    )
    if guild_payload is not None:
        bot._cache_guild(Guild.from_dict(guild_payload, bot=bot))

    await bot.events.dispatch(INTERNAL_EVENT_NAME, member)
