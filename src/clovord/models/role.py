from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils.payload import unwrap_payload
from ._helpers import optional_bool, optional_int, optional_str, snowflake_str


@dataclass(slots=True)
class Role:
    id: str
    name: str
    guild_id: str | None = None
    color: int = 0
    hoist: bool = False
    position: int = 0
    permissions: int = 0
    managed: bool = False
    mentionable: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    _bot: Any = field(repr=False, default=None)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None, *, guild_id: str | None = None, bot: Any = None) -> Role:
        data = payload if isinstance(payload, dict) else {}
        permissions_value = data.get("permissions")
        if isinstance(permissions_value, str) and permissions_value.isdigit():
            permissions = int(permissions_value)
        else:
            permissions = optional_int(permissions_value) or 0

        return cls(
            id=snowflake_str(data.get("id")),
            name=optional_str(data.get("name")) or "unknown",
            guild_id=optional_str(data.get("guild_id")) or guild_id,
            color=optional_int(data.get("color")) or 0,
            hoist=optional_bool(data.get("hoist")),
            position=optional_int(data.get("position")) or 0,
            permissions=permissions,
            managed=optional_bool(data.get("managed")),
            mentionable=optional_bool(data.get("mentionable")),
            raw=dict(data),
            _bot=bot,
        )

    def _require_bot(self) -> Any:
        if self._bot is None:
            raise RuntimeError("Role is missing bot context")
        return self._bot

    def _require_guild_id(self) -> str:
        if not self.guild_id:
            raise RuntimeError("Role is missing guild_id")
        return self.guild_id

    async def edit(
        self,
        *,
        name: str | None = None,
        color: int | None = None,
        hoist: bool | None = None,
        mentionable: bool | None = None,
        permissions: int | str | None = None,
        position: int | None = None,
        **extra: Any,
    ) -> Role:
        bot = self._require_bot()
        guild_id = self._require_guild_id()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if color is not None:
            body["color"] = int(color)
        if hoist is not None:
            body["hoist"] = bool(hoist)
        if mentionable is not None:
            body["mentionable"] = bool(mentionable)
        if permissions is not None:
            body["permissions"] = str(permissions)
        if position is not None:
            body["position"] = int(position)
        if extra:
            body.update(extra)
        if not body:
            raise ValueError("edit requires at least one field")

        response = await bot.http.patch(f"/guilds/{guild_id}/roles/{self.id}", json=body)
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("Role.edit returned a non-object payload")
        return Role.from_dict(payload, guild_id=guild_id, bot=bot)

    async def delete(self) -> None:
        bot = self._require_bot()
        guild_id = self._require_guild_id()
        await bot.http.delete(f"/guilds/{guild_id}/roles/{self.id}")
