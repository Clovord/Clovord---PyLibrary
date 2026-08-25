from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ... import __version__
from ...utils.library_autoupdate import apply_library_autoupdate, is_python_library
from ...utils.logger import get_logger
from ...utils.pypi import is_version_outdated

if TYPE_CHECKING:
    from ...bot import Bot

GATEWAY_EVENT_NAME = "LIBRARY_UPDATE"
INTERNAL_EVENT_NAME = "on_library_update"


logger = get_logger("LibraryUpdater")


def _normalize_release_version(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized or normalized.lower() in {"main", "master", "unknown"}:
        return None
    return normalized


async def handle(bot: Bot, data_full: dict | None = None, data_part: dict | None = None) -> None:
    payload = data_part if isinstance(data_part, dict) else {}

    library = payload.get("library") or "clovord.py"
    if not is_python_library(library):
        return

    new_version = _normalize_release_version(payload.get("version"))
    current_version = payload.get("current_version") or __version__
    download_url = payload.get("download_url")
    commit = payload.get("commit")
    message = payload.get("message")

    if new_version and current_version and not is_version_outdated(current_version, new_version):
        return

    if new_version and not download_url:
        download_url = f"https://pypi.org/project/clovord.py/{new_version}/"

    log_message = (
        "=== LIBRARY UPDATE AVAILABLE ===\n"
        f"Library: {library}\n"
        f"Current Version: {current_version or 'unknown'}\n"
        f"New Version: {new_version or 'unknown'}\n"
        f"Commit: {commit or 'N/A'}\n"
        f"Message: {message or 'No release message provided.'}\n"
        f"Download URL: {download_url or 'N/A'}\n"
        "================================"
    )
    logger.info(log_message)

    await bot.events.dispatch(INTERNAL_EVENT_NAME, payload)

    if getattr(bot, "autoupdate", False):
        await apply_library_autoupdate(bot, version=new_version)
