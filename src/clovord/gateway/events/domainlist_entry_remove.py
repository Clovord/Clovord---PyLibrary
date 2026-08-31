from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...models.domainlist import DomainlistEntry

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "DOMAINLIST_ENTRY_REMOVE"
INTERNAL_EVENT_NAME = "on_domainlist_entry_remove"


def _extract_entry(data_part: dict | None) -> Any:
    if isinstance(data_part, dict) and "entry" in data_part:
        return data_part.get("entry")
    return data_part


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    entry = _extract_entry(data_part if isinstance(data_part, dict) else None)
    if isinstance(entry, dict):
        await bot.events.dispatch(INTERNAL_EVENT_NAME, DomainlistEntry.from_dict(entry))
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, entry)
