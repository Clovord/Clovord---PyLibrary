from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "DOMAINLIST_ENTRY_UPDATE"
INTERNAL_EVENT_NAME = "on_domainlist_entry_update"


def _extract_entry(data_part: dict | None) -> Any:
    if isinstance(data_part, dict) and "entry" in data_part:
        return data_part.get("entry")
    return data_part


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    await bot.events.dispatch(INTERNAL_EVENT_NAME, _extract_entry(data_part))
