from __future__ import annotations

from typing import TYPE_CHECKING, Any


from ...models.message import Message
from ...utils.logger import get_logger
if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GATEWAY_SHUTDOWN"
INTERNAL_EVENT_NAME = "on_shutdown"

logger = get_logger("GatewayShutdown")
async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    logger.info("=== GATEWAY SHUTDOWN ===")

    log_message = (
        "=== GATEWAY SHUTDOWN ===\n"
        "The gateway is shutting down.\n"
        "================================"
    )
    logger.info(log_message)

    await bot.events.dispatch(INTERNAL_EVENT_NAME)
