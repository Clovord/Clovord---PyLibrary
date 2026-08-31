from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.channel import Channel

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "CHANNEL_UPDATE"
INTERNAL_EVENT_NAME = "on_channel_update"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if isinstance(data_part, dict):
        channel = Channel.from_dict(data_part, bot=bot)
        await bot.events.dispatch(INTERNAL_EVENT_NAME, channel)
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
