from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import optional_bool, optional_int, optional_str, snowflake_str


@dataclass(slots=True)
class User:
    id: str
    username: str
    global_name: str | None = None
    discriminator: str | None = None
    avatar: str | None = None
    banner: str | None = None
    accent_color: int | None = None
    flags: int = 0
    bot: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> User:
        data = payload if isinstance(payload, dict) else {}
        username = (
            optional_str(data.get("username"))
            or optional_str(data.get("name"))
            or optional_str(data.get("display_name"))
            or "unknown"
        )
        return cls(
            id=snowflake_str(data.get("id")),
            username=username,
            global_name=optional_str(data.get("global_name")) or optional_str(data.get("display_name")),
            discriminator=optional_str(data.get("discriminator")),
            avatar=optional_str(data.get("avatar")),
            banner=optional_str(data.get("banner")),
            accent_color=optional_int(data.get("accent_color")),
            flags=optional_int(data.get("flags")) or 0,
            bot=optional_bool(data.get("bot")),
            raw=dict(data),
        )

    @property
    def display_name(self) -> str:
        return self.global_name or self.username

    @property
    def mention(self) -> str:
        return f"<@{self.id}>"
