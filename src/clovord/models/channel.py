from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..utils.payload import unwrap_payload
from ._helpers import optional_str, snowflake_str

if TYPE_CHECKING:
    from .message import Message


@dataclass(slots=True)
class Channel:
    id: str
    guild_id: str | None = None
    name: str | None = None
    type: int | None = None
    _bot: Any = field(repr=False, default=None)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None, *, bot: Any = None) -> Channel:
        data = payload if isinstance(payload, dict) else {}
        channel_type = data.get("type")
        guild_payload = data.get("guild") if isinstance(data.get("guild"), dict) else {}
        guild_id = optional_str(data.get("guild_id")) or optional_str(guild_payload.get("id"))
        return cls(
            id=snowflake_str(data.get("id")),
            guild_id=guild_id,
            name=optional_str(data.get("name")),
            type=int(channel_type) if channel_type is not None else None,
            _bot=bot,
            raw=dict(data),
        )

    def _require_bot(self) -> Any:
        if self._bot is None:
            raise RuntimeError("Channel is missing bot context")
        return self._bot

    async def fetch(self) -> Channel:
        """Fetch the latest channel object from the API."""
        bot = self._require_bot()
        response = await bot.http.get(f"/channels/{self.id}")
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("Channel fetch returned a non-object payload")
        return Channel.from_dict(payload, bot=bot)

    async def history(
        self,
        *,
        limit: int = 20,
        before: str | None = None,
    ) -> list[Message]:
        """Fetch recent messages from this channel."""
        from .message import Message

        bot = self._require_bot()
        params: dict[str, Any] = {"limit": int(limit)}
        if before is not None:
            params["before"] = str(before)
        response = await bot.http.get(f"/channels/{self.id}/messages", params=params)
        payload = unwrap_payload(response)
        rows: list[Any]
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
            rows = payload["messages"]
        elif isinstance(payload, list):
            rows = payload
        else:
            rows = []
        return [Message.from_dict(row, bot=bot) for row in rows if isinstance(row, dict)]

    async def send(
        self,
        content: str = "",
        *,
        embeds: list[dict[str, Any]] | None = None,
        components: list[dict[str, Any]] | None = None,
        container: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        reply_to: str | None = None,
        message_reference: dict[str, Any] | None = None,
        allowed_mentions: dict[str, Any] | None = None,
        **extra: Any,
    ) -> Message:
        from .message import Message

        bot = self._require_bot()
        payload: dict[str, Any] = {"content": content}
        if embeds is not None:
            payload["embeds"] = embeds
        if components is not None:
            payload["components"] = components
        elif container is not None:
            payload["components"] = [container]
        if attachments is not None:
            payload["attachments"] = attachments
        if message_reference is not None:
            payload["message_reference"] = message_reference
        elif reply_to is not None:
            payload["message_reference"] = {"message_id": str(reply_to)}
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if extra:
            payload.update(extra)

        response = await bot.http.post(f"/channels/{self.id}/messages", json=payload)
        body = unwrap_payload(response)
        if not isinstance(body, dict):
            raise TypeError("Channel.send returned a non-object payload")
        return Message.from_dict(body, bot=bot)

    async def trigger_typing(self) -> Any:
        """Post a typing indicator to this channel."""
        bot = self._require_bot()
        return await bot.http.post(f"/channels/{self.id}/typing")
