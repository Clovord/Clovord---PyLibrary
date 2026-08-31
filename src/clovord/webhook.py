from __future__ import annotations

from typing import Any

from .http import HTTPClient
from .utils.payload import unwrap_payload
from .ui.components import has_layout_components, serialize_components


class Webhook:
    """Execute messages through a Clovord webhook URL."""

    def __init__(
        self,
        http: HTTPClient,
        webhook_id: str,
        token: str,
        *,
        channel_id: str | None = None,
        guild_id: str | None = None,
    ) -> None:
        self._http = http
        self.id = str(webhook_id)
        self.token = str(token)
        self.channel_id = channel_id
        self.guild_id = guild_id

    @property
    def _path(self) -> str:
        return f"/webhooks/{self.id}/{self.token}"

    async def send(
        self,
        content: str | None = None,
        *,
        username: str | None = None,
        avatar_url: str | None = None,
        components: list[Any] | None = None,
        wait: bool = False,
        tts: bool = False,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"tts": bool(tts)}
        if content is not None:
            body["content"] = content
        if username is not None:
            body["username"] = username
        if avatar_url is not None:
            body["avatar_url"] = avatar_url
        if components is not None:
            body["components"] = serialize_components(components)

        params = {"wait": "true"} if wait else None
        response = await self._http.post(self._path, json=body, params=params, auth=False)
        payload = unwrap_payload(response)
        return payload if isinstance(payload, dict) else {"raw": payload}

    @classmethod
    def from_url(cls, http: HTTPClient, url: str) -> Webhook:
        """Create a webhook client from ``https://clovord.com/api/v2/webhooks/{id}/{token}``."""
        normalized = url.strip().rstrip("/")
        if "/webhooks/" not in normalized:
            raise ValueError("Webhook URL must contain /webhooks/{id}/{token}")
        tail = normalized.split("/webhooks/", 1)[1]
        webhook_id, _, token = tail.partition("/")
        if not webhook_id or not token:
            raise ValueError("Webhook URL is missing id or token")
        return cls(http, webhook_id, token)
