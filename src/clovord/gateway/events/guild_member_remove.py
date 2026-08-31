from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.member import Member

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GUILD_MEMBER_REMOVE"
INTERNAL_EVENT_NAME = "on_guild_member_remove"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if not isinstance(data_part, dict):
        await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
        return

    guild_id = None
    if isinstance(data_part.get("guild"), dict):
        guild_id = str(data_part["guild"].get("id") or "")
    elif data_part.get("guild_id") is not None:
        guild_id = str(data_part.get("guild_id"))

    member_payload = data_part.get("member") if isinstance(data_part.get("member"), dict) else data_part
    user_payload = data_part.get("user") if isinstance(data_part.get("user"), dict) else None
    member = Member.from_dict(member_payload, guild_id=guild_id, user=user_payload, bot=bot)
    await bot.events.dispatch(INTERNAL_EVENT_NAME, member)
