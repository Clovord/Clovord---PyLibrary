"""Clovord Python SDK."""

from importlib.metadata import PackageNotFoundError, version

from .bot import Bot
from .commands import CommandTree, Interaction, InteractionFollowup, InteractionResponse
from .errors import ClovordError, ClovordExtensionError
from .intents import Intents
from .models import (
    Channel,
    DomainlistEntry,
    Guild,
    Member,
    Message,
    PartialMessage,
    Role,
    Typing,
    User,
)
from .ui import ActionRow, Button, Container, Separator, TextDisplay
from .utils.time import format_relative_timestamp, format_timestamp, format_uptime
from .webhook import Webhook

__all__ = [
    "Bot",
    "CommandTree",
    "Interaction",
    "InteractionFollowup",
    "InteractionResponse",
    "ClovordError",
    "ClovordExtensionError",
    "Intents",
    "Channel",
    "DomainlistEntry",
    "Guild",
    "Member",
    "Message",
    "PartialMessage",
    "Role",
    "Typing",
    "User",
    "ActionRow",
    "Button",
    "Container",
    "Separator",
    "TextDisplay",
    "format_uptime",
    "format_timestamp",
    "format_relative_timestamp",
    "Webhook",
]

try:
    __version__ = version("clovord.py")
except PackageNotFoundError:
    # Fallback for source-tree usage where distribution metadata is unavailable.
    __version__ = "0.0.0"
