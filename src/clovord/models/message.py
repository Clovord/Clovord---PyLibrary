from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.payload import unwrap_payload
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
        guild_payload = payload.get("guild") if isinstance(payload.get("guild"), dict) else {}
        guild_id = optional_str(payload.get("guild_id")) or optional_str(guild_payload.get("id"))
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

    def _require_bot(self) -> Any:
        if self.channel._bot is None:
            raise RuntimeError("Message is missing bot context")
        return self.channel._bot

    async def edit(
        self,
        content: str | None = None,
        *,
        components: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> Message:
        """Edit this message."""
        bot = self._require_bot()
        body: dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if components is not None:
            body["components"] = components
        if extra:
            body.update(extra)
        if not body:
            raise ValueError("edit requires at least one field")

        response = await bot.http.patch(
            f"/channels/{self.channel_id}/messages/{self.id}",
            json=body,
        )
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("Message.edit returned a non-object payload")
        return Message.from_dict(payload, bot=bot)

    async def delete(self) -> None:
        """Delete this message."""
        bot = self._require_bot()
        await bot.http.delete(f"/channels/{self.channel_id}/messages/{self.id}")
