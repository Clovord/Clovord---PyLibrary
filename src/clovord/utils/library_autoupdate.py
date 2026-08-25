from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING, Any

from .logger import get_logger

if TYPE_CHECKING:
    from ..bot import Bot

_PACKAGE_NAME = "clovord.py"
_PYTHON_LIBRARY_NAMES = frozenset({"clovord.py", "python", "py", "clovord"})

logger = get_logger("LibraryUpdater")


def is_python_library(library: Any) -> bool:
    name = str(library or "").strip().lower()
    return not name or name in _PYTHON_LIBRARY_NAMES


def _package_spec(version: str | None) -> str:
    normalized = str(version or "").strip()
    if normalized:
        return f"{_PACKAGE_NAME}=={normalized}"
    return _PACKAGE_NAME


async def apply_library_autoupdate(bot: Bot, *, version: str | None = None) -> bool:
    """Install the latest clovord.py from PyPI and replace the current process.

    Returns ``True`` when a restart was initiated (process will be replaced).
    """
    if getattr(bot, "_library_autoupdate_started", False):
        return False

    if getattr(sys, "frozen", False):
        logger.warning(
            "autoupdate is enabled but the process looks frozen/packaged; "
            "skipping automatic pip install and restart"
        )
        return False

    bot._library_autoupdate_started = True
    package_spec = _package_spec(version)
    logger.info("autoupdate enabled — installing %s via pip", package_spec)

    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            package_spec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
    except Exception:
        bot._library_autoupdate_started = False
        logger.exception("autoupdate failed while launching pip for %s", package_spec)
        return False

    if process.returncode != 0:
        bot._library_autoupdate_started = False
        detail = (stderr or stdout or b"").decode("utf-8", errors="replace").strip()
        logger.error(
            "autoupdate pip install failed (exit=%s): %s",
            process.returncode,
            detail or "no output",
        )
        return False

    logger.info("autoupdate installed %s — restarting bot process", package_spec)

    try:
        await bot.close()
    except Exception:
        logger.exception("autoupdate could not close the bot cleanly before restart")

    argv = [sys.executable, *sys.argv]
    try:
        os.execv(sys.executable, argv)
    except Exception:
        bot._library_autoupdate_started = False
        logger.exception("autoupdate installed the package but failed to restart the process")
        return False

    # Unreachable when execv succeeds; kept for type checkers.
    return True
