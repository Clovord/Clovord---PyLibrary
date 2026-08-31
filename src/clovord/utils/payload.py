from __future__ import annotations

from typing import Any


def unwrap_payload(response: dict[str, Any] | list[Any] | None) -> Any:
    """Extract the useful body from a Clovord API envelope."""
    if not isinstance(response, dict):
        return response
    for key in ("payload", "data", "commands"):
        if key in response:
            return response[key]
    return response
