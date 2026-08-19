from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ..gateway.events import library_update
from .pypi import fetch_pypi_latest_version, is_version_outdated

if TYPE_CHECKING:
    from ..bot import Bot

_PYPI_PROJECT_URL = "https://pypi.org/project/clovord.py/"


def _installed_version() -> str:
    try:
        return str(version("clovord.py")).strip()
    except PackageNotFoundError:
        return "0.0.0"


async def check_and_notify_library_update(bot: Bot) -> None:
    if getattr(bot, "_library_update_notice_sent", False):
        return

    current_version = _installed_version()
    if not current_version or current_version == "0.0.0":
        return

    latest_version = await fetch_pypi_latest_version("clovord.py")
    if not latest_version or not is_version_outdated(current_version, latest_version):
        return

    bot._library_update_notice_sent = True
    await library_update.handle(
        bot,
        data_part={
            "library": "clovord.py",
            "version": latest_version,
            "current_version": current_version,
            "download_url": _PYPI_PROJECT_URL,
            "message": (
                f"A new clovord.py release is available ({latest_version}). "
                f"You are running {current_version}."
            ),
            "source": "pypi",
        },
    )
