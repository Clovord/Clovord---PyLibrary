from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import optional_str, snowflake_str


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
        return cls(
            id=snowflake_str(data.get("id")),
            guild_id=optional_str(data.get("guild_id")),
            name=optional_str(data.get("name")),
            type=int(channel_type) if channel_type is not None else None,
            _bot=bot,
            raw=dict(data),
        )

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
    ) -> dict[str, Any]:
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

        return await self._bot.http.post(f"/channels/{self.id}/messages", json=payload)

    async def trigger_typing(self) -> Any:
        """Post a typing indicator to this channel."""
        return await self._bot.http.post(f"/channels/{self.id}/typing")
