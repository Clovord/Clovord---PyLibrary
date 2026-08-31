from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ._helpers import optional_str, parse_timestamp, snowflake_str
from .user import User


@dataclass(slots=True)
class Typing:
    channel_id: str
    guild_id: str | None = None
    user: User | None = None
    timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> Typing:
        data = payload if isinstance(payload, dict) else {}
        user_payload = data.get("user") if isinstance(data.get("user"), dict) else None
        return cls(
            channel_id=snowflake_str(data.get("channel_id")),
            guild_id=optional_str(data.get("guild_id")),
            user=User.from_dict(user_payload) if user_payload is not None else None,
            timestamp=parse_timestamp(data.get("timestamp")),
            raw=dict(data),
        )
