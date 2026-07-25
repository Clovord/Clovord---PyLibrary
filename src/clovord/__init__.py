"""Clovord Python SDK."""

from importlib.metadata import PackageNotFoundError, version

from .bot import Bot
from .commands import CommandTree, Interaction, InteractionResponse
from .errors import ClovordError, ClovordExtensionError
from .intents import Intents
from .ui import ActionRow, Button, Container, Separator, TextDisplay

__all__ = [
    "Bot",
    "CommandTree",
    "Interaction",
    "InteractionResponse",
    "ClovordError",
    "ClovordExtensionError",
    "Intents",
    "ActionRow",
    "Button",
    "Container",
    "Separator",
    "TextDisplay",
]

try:
    __version__ = version("clovord.py")
except PackageNotFoundError:
    # Fallback for source-tree usage where distribution metadata is unavailable.
    __version__ = "0.0.0"
