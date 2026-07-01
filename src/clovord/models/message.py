from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .channel import Channel
from .user import User


@dataclass(slots=True)
class Message:
    id: str
    content: str
    author: User
    channel: Channel

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, bot: Any) -> "Message":
        author_payload = payload.get("author") if isinstance(payload.get("author"), dict) else {}

        channel_payload = payload.get("channel") if isinstance(payload.get("channel"), dict) else {}
        channel_id = channel_payload.get("id") or payload.get("channel_id") or ""
        return cls(
            id=str(payload.get("id", "")),
            content=str(payload.get("content", "")),
            author=User.from_dict(author_payload),
            channel=Channel(id=str(channel_id), _bot=bot),
        )
