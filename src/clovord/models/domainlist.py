from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import optional_int, optional_str, snowflake_str


@dataclass(slots=True)
class DomainlistEntry:
    """Clovord domainlist entry delivered by DOMAINLIST_* gateway events."""

    domain: str
    hash: str | None = None
    status: str | None = None
    score: int = 0
    flags: int = 0
    subdomain: str | None = None
    slug: str | None = None
    tags: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    record_updated: str | None = None
    record_added: str | None = None
    history: Any = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> DomainlistEntry:
        data = payload if isinstance(payload, dict) else {}
        metadata = data.get("metadata")
        return cls(
            domain=optional_str(data.get("domain")) or "",
            hash=optional_str(data.get("hash")),
            status=optional_str(data.get("status")),
            score=optional_int(data.get("score")) or 0,
            flags=optional_int(data.get("flags")) or 0,
            subdomain=optional_str(data.get("subdomain")),
            slug=optional_str(data.get("slug")),
            tags=optional_str(data.get("tags")),
            metadata=dict(metadata) if isinstance(metadata, dict) else {},
            record_updated=optional_str(data.get("record_updated")),
            record_added=optional_str(data.get("record_added")),
            history=data.get("history"),
            raw=dict(data),
        )
