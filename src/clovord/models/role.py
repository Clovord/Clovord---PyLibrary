from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None, *, guild_id: str | None = None) -> Role:
        data = payload if isinstance(payload, dict) else {}
        return cls(
            id=snowflake_str(data.get("id")),
            name=optional_str(data.get("name")) or "unknown",
            guild_id=optional_str(data.get("guild_id")) or guild_id,
            color=optional_int(data.get("color")) or 0,
            hoist=optional_bool(data.get("hoist")),
            position=optional_int(data.get("position")) or 0,
            permissions=optional_int(data.get("permissions")) or 0,
            managed=optional_bool(data.get("managed")),
            mentionable=optional_bool(data.get("mentionable")),
            raw=dict(data),
        )
