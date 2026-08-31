from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.message import PartialMessage

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "MESSAGE_DELETE"
INTERNAL_EVENT_NAME = "on_message_delete"


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if isinstance(data_part, dict):
        message = PartialMessage.from_dict(data_part)
        await bot.events.dispatch(INTERNAL_EVENT_NAME, message)
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
