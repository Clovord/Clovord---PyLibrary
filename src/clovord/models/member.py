from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.payload import unwrap_payload
from ._helpers import optional_str, parse_timestamp, snowflake_str
from .user import User


@dataclass(slots=True)
class Member:
    user: User
    guild_id: str
    nick: str | None = None
    roles: list[str] = field(default_factory=list)
    joined_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    _bot: Any = field(repr=False, default=None)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any] | None,
        *,
        guild_id: str | None = None,
        user: dict[str, Any] | None = None,
        bot: Any = None,
    ) -> Member:
        data = payload if isinstance(payload, dict) else {}
        resolved_guild_id = (
            optional_str(data.get("guild_id"))
            or guild_id
            or snowflake_str(data.get("guild", {}).get("id") if isinstance(data.get("guild"), dict) else None)
        )

        user_payload = user
        if user_payload is None and isinstance(data.get("user"), dict):
            user_payload = data["user"]
        elif user_payload is None and data.get("id") is not None and data.get("username") is not None:
            user_payload = data

        roles_value = data.get("roles")
        roles: list[str] = []
        if isinstance(roles_value, list):
            roles = [snowflake_str(role) for role in roles_value if role is not None]

        return cls(
            user=User.from_dict(user_payload),
            guild_id=snowflake_str(resolved_guild_id),
            nick=optional_str(data.get("nick")) or optional_str(data.get("nickname")),
            roles=roles,
            joined_at=parse_timestamp(data.get("joined_at")),
            raw=dict(data),
            _bot=bot,
        )

    @property
    def id(self) -> str:
        return self.user.id

    @property
    def display_name(self) -> str:
        return self.nick or self.user.display_name

    def _require_bot(self) -> Any:
        if self._bot is None:
            raise RuntimeError("Member is missing bot context")
        return self._bot

    async def edit(
        self,
        *,
        nick: str | None = None,
        roles: list[str] | None = None,
        mute: dict[str, Any] | None = None,
    ) -> Member:
        bot = self._require_bot()
        body: dict[str, Any] = {}
        if nick is not None:
            body["nick"] = nick
        if roles is not None:
            body["roles"] = [str(role) for role in roles]
        if mute is not None:
            body["mute"] = mute
        if not body:
            raise ValueError("edit requires at least one field")

        response = await bot.http.patch(
            f"/guilds/{self.guild_id}/members/{self.id}",
            json=body,
        )
        payload = unwrap_payload(response)
        if isinstance(payload, dict) and isinstance(payload.get("member"), dict):
            return Member.from_dict(payload["member"], guild_id=self.guild_id, bot=bot)
        if isinstance(payload, dict):
            return Member.from_dict(payload, guild_id=self.guild_id, bot=bot)
        raise TypeError("Member.edit returned a non-object payload")
