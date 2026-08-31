from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import optional_int, optional_str, snowflake_str


@dataclass(slots=True)
class DomainlistEntry:
    """Clovord domainlist entry from gateway events or REST search."""

    domain: str
    hash: str | None = None
    status: str | None = None
    score: int = 0
    flags: int = 0
    subdomain: str | None = None
    slug: str | None = None
    tags: str | None = None
    reason: str | None = None
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    record_updated: str | None = None
    record_added: str | None = None
    history: Any = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def host(self) -> str:
        """Fully qualified host (subdomain + domain) when available."""
        domain = self.domain.strip()
        subdomain = (self.subdomain or "").strip().strip(".")
        if subdomain and domain:
            return f"{subdomain}.{domain}"
        return domain

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> DomainlistEntry:
        data = payload if isinstance(payload, dict) else {}
        metadata = data.get("metadata")
        sources = data.get("sources")
        if isinstance(sources, list):
            normalized_sources = [str(item) for item in sources if str(item).strip()]
        else:
            normalized_sources = []
        return cls(
            domain=optional_str(data.get("domain")) or "",
            hash=optional_str(data.get("hash")),
            status=optional_str(data.get("status")),
            score=optional_int(data.get("score")) or 0,
            flags=optional_int(data.get("flags")) or 0,
            subdomain=optional_str(data.get("subdomain")),
            slug=optional_str(data.get("slug")),
            tags=optional_str(data.get("tags")),
            reason=optional_str(data.get("reason")),
            sources=normalized_sources,
            metadata=dict(metadata) if isinstance(metadata, dict) else {},
            record_updated=optional_str(data.get("record_updated")),
            record_added=optional_str(data.get("record_added")),
            history=data.get("history"),
            raw=dict(data),
        )

    @classmethod
    def from_search_response(cls, response: dict[str, Any] | list[Any] | None) -> list[DomainlistEntry]:
        """Parse a Clovord multi-status domain search response."""
        if not isinstance(response, dict):
            return []

        items = response.get("items")
        if isinstance(items, list):
            entries: list[DomainlistEntry] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                data = item.get("data")
                if data is None:
                    data = item.get("payload")
                if isinstance(data, dict):
                    entries.append(cls.from_dict(data))
            return entries

        from ..utils.payload import unwrap_payload

        payload = unwrap_payload(response)
        if isinstance(payload, dict):
            return [cls.from_dict(payload)]
        if isinstance(payload, list):
            return [cls.from_dict(row) for row in payload if isinstance(row, dict)]
        return []
