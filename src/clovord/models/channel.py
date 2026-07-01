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
        container: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        reply_to: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"content": content}
        if embeds is not None:
            payload["embeds"] = embeds
        if container is not None:
            payload["container"] = container
        if attachments is not None:
            payload["attachments"] = attachments
        if reply_to is not None:
            payload["reply_to"] = reply_to
        if extra:
            payload.update(extra)

        return await self._bot.http.post(f"/channels/{self.id}/messages", json=payload)