from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.message import Message

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "DOMAINLIST_ENTRY_CREATE"
INTERNAL_EVENT_NAME = "on_domainlist_entry_create"

async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
