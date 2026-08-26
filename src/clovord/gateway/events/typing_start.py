from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "TYPING_START"
INTERNAL_EVENT_NAME = "on_typing_start"


def _to_object(value: Any) -> Any:
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _to_object(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_to_object(v) for v in value]
    return value


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    if not isinstance(data_part, dict):
        await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
        return

    await bot.events.dispatch(INTERNAL_EVENT_NAME, _to_object(data_part))
