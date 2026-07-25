from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot


async def handle(bot: Bot, data_full: Any, data_part: Any) -> None:
    await bot.events.dispatch("on_interaction_create", data_full, data_part)
