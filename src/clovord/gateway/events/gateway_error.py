from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...utils.logger import get_logger

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "GATEWAY_ERROR"
INTERNAL_EVENT_NAME = "on_gateway_error"

logger = get_logger()


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    payload = data_part if isinstance(data_part, dict) else {}
    request = payload.get("request") if isinstance(payload.get("request"), dict) else {}
    status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    errors = payload.get("errors") if isinstance(payload.get("errors"), dict) else {}

    event = request.get("event", "UNKNOWN_EVENT")
    code = status.get("code", "UNKNOWN_CODE")
    message = status.get("code_message") or errors.get("custom_message") or "UNKNOWN_MESSAGE"
    custom_message = errors.get("custom_message")

    if custom_message and str(custom_message) != str(message):
        logger.error(
            "Gateway error: event=%s code=%s message=%s detail=%s",
            event,
            code,
            message,
            custom_message,
        )
    else:
        logger.error("Gateway error: event=%s code=%s message=%s", event, code, message)

    await bot.events.dispatch(INTERNAL_EVENT_NAME, payload)
