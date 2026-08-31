from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.member import Member

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GUILD_MEMBER_UPDATE"
INTERNAL_EVENT_NAME = "on_guild_member_update"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if isinstance(data_part, dict):
        guild_id = None
        if isinstance(data_part.get("guild"), dict):
            guild_id = str(data_part["guild"].get("id") or "")
        member = Member.from_dict(data_part.get("member") if isinstance(data_part.get("member"), dict) else data_part, guild_id=guild_id, bot=bot)
        await bot.events.dispatch(INTERNAL_EVENT_NAME, member)
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
