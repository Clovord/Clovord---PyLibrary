from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Channel:
    id: str
    _bot: Any = field(repr=False)

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
            # Legacy alias: single container becomes a top-level components list
            payload["components"] = [container]
        if attachments is not None:
            payload["attachments"] = attachments
        if message_reference is not None:
            payload["message_reference"] = message_reference
        elif reply_to is not None:
            # Legacy alias → Discord message_reference
            payload["message_reference"] = {"message_id": str(reply_to)}
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if extra:
            payload.update(extra)

        return await self._bot.http.post(f"/channels/{self.id}/messages", json=payload)
