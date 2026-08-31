from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ._helpers import optional_int, optional_str, parse_timestamp, snowflake_str


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
