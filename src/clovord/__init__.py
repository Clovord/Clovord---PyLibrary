"""Clovord Python SDK."""

from importlib.metadata import PackageNotFoundError, version

from .bot import Bot
from .errors import ClovordError
from .intents import Intents

__all__ = ["Bot", "ClovordError", "Intents"]

try:
    __version__ = version("clovord.py")
except PackageNotFoundError:
    # Fallback for source-tree usage where distribution metadata is unavailable.
    __version__ = "0.0.0"
