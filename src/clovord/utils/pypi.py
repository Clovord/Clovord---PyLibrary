from __future__ import annotations

import re
from typing import Any

import aiohttp

_PYPI_PACKAGE_URL = "https://pypi.org/pypi/{package}/json"
_VERSION_PART = re.compile(r"(\d+)")


def parse_version(value: str | None) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        return (0,)

    parts: list[int] = []
    for segment in text.split("."):
        segment = segment.split("-")[0].split("+")[0]
        match = _VERSION_PART.match(segment)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts) if parts else (0,)


def is_version_outdated(current: str | None, latest: str | None) -> bool:
    current_parts = parse_version(current)
    latest_parts = parse_version(latest)
    if current_parts == latest_parts:
        return False
    return current_parts < latest_parts


async def fetch_pypi_latest_version(
    package: str,
    *,
    session: aiohttp.ClientSession | None = None,
    timeout_seconds: float = 5.0,
) -> str | None:
    package_name = str(package or "").strip()
    if not package_name:
        return None

    url = _PYPI_PACKAGE_URL.format(package=package_name)
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    if session is not None and not session.closed:
        return await _read_pypi_version(session, url, timeout=timeout)

    async with aiohttp.ClientSession(timeout=timeout) as owned_session:
        return await _read_pypi_version(owned_session, url, timeout=timeout)


async def _read_pypi_version(
    session: aiohttp.ClientSession,
    url: str,
    *,
    timeout: aiohttp.ClientTimeout,
) -> str | None:
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            payload: Any = await response.json()
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    info = payload.get("info")
    if not isinstance(info, dict):
        return None
    version = str(info.get("version") or "").strip()
    return version or None
