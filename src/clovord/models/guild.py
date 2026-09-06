from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.payload import unwrap_payload
from ._helpers import optional_int, optional_str, parse_timestamp, snowflake_str
from .channel import Channel
from .member import Member
from .role import Role


@dataclass(slots=True)
class Guild:
    id: str
    name: str
    owner_id: str | None = None
    icon: str | None = None
    description: str | None = None
    banner_color: int | None = None
    flags: int = 0
    features: list[str] = field(default_factory=list)
    unavailable: bool = False
    created_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    _bot: Any = field(repr=False, default=None)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None, *, bot: Any = None) -> Guild:
        data = payload if isinstance(payload, dict) else {}
        features = data.get("features")
        if isinstance(features, list):
            normalized_features = [str(item) for item in features if str(item).strip()]
        else:
            normalized_features = []

        return cls(
            id=snowflake_str(data.get("id")),
            name=optional_str(data.get("name")) or "Unknown Guild",
            owner_id=optional_str(data.get("owner_id")),
            icon=optional_str(data.get("icon")),
            description=optional_str(data.get("description")),
            banner_color=optional_int(data.get("banner_color")),
            flags=optional_int(data.get("flags")) or 0,
            features=normalized_features,
            unavailable=bool(data.get("unavailable")),
            created_at=parse_timestamp(data.get("created_at")),
            raw=dict(data),
            _bot=bot,
        )

    def _require_bot(self) -> Any:
        if self._bot is None:
            raise RuntimeError("Guild is missing bot context")
        return self._bot

    async def fetch(self, *, with_counts: bool = False) -> Guild:
        bot = self._require_bot()
        params = {"with_counts": "true"} if with_counts else None
        response = await bot.http.get(f"/guilds/{self.id}", params=params)
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("Guild.fetch returned a non-object payload")
        return Guild.from_dict(payload, bot=bot)

    async def fetch_channels(self) -> list[Channel]:
        bot = self._require_bot()
        response = await bot.http.get(f"/guilds/{self.id}/channels")
        payload = unwrap_payload(response)
        rows: list[Any]
        if isinstance(payload, dict) and isinstance(payload.get("channels"), list):
            rows = payload["channels"]
        elif isinstance(payload, list):
            rows = payload
        else:
            rows = []
        return [Channel.from_dict(row, bot=bot) for row in rows if isinstance(row, dict)]

    async def fetch_members(
        self,
        *,
        limit: int = 500,
        after: str | None = None,
        online: bool | None = None,
    ) -> list[Member]:
        bot = self._require_bot()
        params: dict[str, Any] = {"limit": int(limit)}
        if after is not None:
            params["after"] = str(after)
        if online is not None:
            params["online"] = "true" if online else "false"
        response = await bot.http.get(f"/guilds/{self.id}/members", params=params)
        payload = unwrap_payload(response)
        rows: list[Any] = []
        if isinstance(payload, dict) and isinstance(payload.get("members"), list):
            rows = payload["members"]
        return [Member.from_dict(row, guild_id=self.id, bot=bot) for row in rows if isinstance(row, dict)]

    async def fetch_member(self, user_id: str) -> Member:
        bot = self._require_bot()
        response = await bot.http.get(f"/guilds/{self.id}/members/{user_id}")
        payload = unwrap_payload(response)
        if isinstance(payload, dict) and isinstance(payload.get("member"), dict):
            return Member.from_dict(payload["member"], guild_id=self.id, bot=bot)
        if isinstance(payload, dict):
            return Member.from_dict(payload, guild_id=self.id, bot=bot)
        raise TypeError("Guild.fetch_member returned a non-object payload")

    async def fetch_roles(self) -> list[Role]:
        bot = self._require_bot()
        response = await bot.http.get(f"/guilds/{self.id}/roles")
        payload = unwrap_payload(response)
        rows: list[Any] = []
        if isinstance(payload, dict) and isinstance(payload.get("roles"), list):
            rows = payload["roles"]
        return [Role.from_dict(row, guild_id=self.id, bot=bot) for row in rows if isinstance(row, dict)]

    async def create_role(
        self,
        *,
        name: str,
        color: int = 0,
        hoist: bool = False,
        mentionable: bool = False,
        permissions: int | str = 0,
        flags: int = 0,
    ) -> Role:
        bot = self._require_bot()
        body = {
            "name": name,
            "color": int(color),
            "hoist": bool(hoist),
            "mentionable": bool(mentionable),
            "permissions": str(permissions),
            "flags": int(flags),
        }
        response = await bot.http.post(f"/guilds/{self.id}/roles", json=body)
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("Guild.create_role returned a non-object payload")
        return Role.from_dict(payload, guild_id=self.id, bot=bot)

    async def kick(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        note: str | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        bot = self._require_bot()
        body: dict[str, Any] = {"silent": bool(silent)}
        if reason is not None:
            body["reason"] = reason
        if note is not None:
            body["note"] = note
        response = await bot.http.delete(f"/guilds/{self.id}/users/{user_id}", json=body)
        payload = unwrap_payload(response)
        return payload if isinstance(payload, dict) else {"raw": payload}

    async def ban(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        duration: str | None = None,
        note: str | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        bot = self._require_bot()
        body: dict[str, Any] = {"user_id": str(user_id), "silent": bool(silent)}
        if reason is not None:
            body["reason"] = reason
        if duration is not None:
            body["duration"] = duration
        if note is not None:
            body["note"] = note
        response = await bot.http.post(f"/guilds/{self.id}/bans", json=body)
        payload = unwrap_payload(response)
        return payload if isinstance(payload, dict) else {"raw": payload}

    async def unban(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        bot = self._require_bot()
        params: dict[str, Any] = {}
        if reason is not None:
            params["reason"] = reason
        if silent:
            params["silent"] = "true"
        delete_kwargs: dict[str, Any] = {}
        if params:
            delete_kwargs["params"] = params
        response = await bot.http.delete(
            f"/guilds/{self.id}/bans/{user_id}",
            **delete_kwargs,
        )
        payload = unwrap_payload(response)
        return payload if isinstance(payload, dict) else {"raw": payload}
