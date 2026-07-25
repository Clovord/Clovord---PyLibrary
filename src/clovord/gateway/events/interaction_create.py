from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot


async def handle(bot: Bot, data_full: Any, data_part: Any) -> None:
    payload = data_part if isinstance(data_part, dict) else data_full
    if isinstance(payload, dict) and hasattr(bot, "tree"):
        try:
            handled = await bot.tree.dispatch(payload)
            if handled:
                return
        except Exception:
            # Fall through to user event so errors remain visible there if desired.
            pass
    await bot.events.dispatch("on_interaction_create", data_full, data_part)
