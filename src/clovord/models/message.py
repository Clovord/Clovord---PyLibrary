from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ._helpers import optional_str, parse_timestamp, snowflake_str
from .channel import Channel
from .user import User


@dataclass(slots=True)
class PartialMessage:
    """Lightweight message reference used by delete/update gateway events."""

    id: str
    channel_id: str
    guild_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PartialMessage:
        data = payload if isinstance(payload, dict) else {}
        return cls(
            id=snowflake_str(data.get("id")),
            channel_id=snowflake_str(data.get("channel_id")),
            guild_id=optional_str(data.get("guild_id")),
            raw=dict(data),
        )


@dataclass(slots=True)
class Message:
    id: str
    content: str
    author: User
    channel: Channel
    channel_id: str
    guild_id: str | None = None
    timestamp: datetime | None = None
    edited_timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, bot: Any) -> Message:
        author_payload = payload.get("author") if isinstance(payload.get("author"), dict) else {}
        channel_payload = payload.get("channel") if isinstance(payload.get("channel"), dict) else {}
        channel_id = snowflake_str(channel_payload.get("id") or payload.get("channel_id"))
        guild_id = optional_str(payload.get("guild_id"))
        if guild_id is None and isinstance(channel_payload, dict):
            guild_id = optional_str(channel_payload.get("guild_id"))

        return cls(
            id=snowflake_str(payload.get("id")),
            content=str(payload.get("content", "")),
            author=User.from_dict(author_payload),
            channel=Channel(id=channel_id, guild_id=guild_id, _bot=bot),
            channel_id=channel_id,
            guild_id=guild_id,
            timestamp=parse_timestamp(payload.get("timestamp") or payload.get("created_at")),
            edited_timestamp=parse_timestamp(payload.get("edited_timestamp")),
            raw=dict(payload),
        )
