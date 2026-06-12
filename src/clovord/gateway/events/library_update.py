from __future__ import annotations

from typing import TYPE_CHECKING, Any


from utils.logger import get_logger


from ...models.message import Message

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "LIBRARY_UPDATE"
INTERNAL_EVENT_NAME = "on_library_update"


logger = get_logger("LibraryUpdater")
async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    library = data_part.get("library") if data_part else "Python"
    version = data_part.get("version") if data_part else "unknown"
    download_url = data_part.get("download_url") if data_part else None
    commit = data_part.get("commit") if data_part else None
    message = data_part.get("message") if data_part else None

    log_message = (
        "=== LIBRARY UPDATE AVAILABLE ===\n"
        f"Library: {library}\n"
        f"Version: {version}\n"
        f"Commit: {commit or 'N/A'}\n"
        f"Message: {message or 'No release message provided.'}\n"
        f"Download URL: {download_url or 'N/A'}\n"
        "================================"
    )
    logger.info(log_message)

    await bot.events.dispatch(INTERNAL_EVENT_NAME, data_part)
