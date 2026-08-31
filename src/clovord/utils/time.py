from __future__ import annotations

from datetime import datetime, timedelta, timezone

TimestampStyle = str


def _normalize_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def format_timestamp(dt: datetime, style: TimestampStyle = "f") -> str:
    """Return a Clovord/Discord-style timestamp marker for ``dt``.

    Common styles:
    - ``R`` relative (``5 minutes ago``)
    - ``f`` short date/time
    - ``F`` long date/time
    - ``t`` short time
    - ``T`` long time
    - ``d`` short date
    - ``D`` long date
    """
    unix = int(_normalize_datetime(dt).timestamp())
    normalized_style = str(style or "f").strip() or "f"
    return f"<t:{unix}:{normalized_style}>"


def format_uptime(delta: timedelta, *, compact: bool = False) -> str:
    """Format a duration for display in bot messages.

    By default returns human-readable text like ``1 hour, 3 minutes, 5 seconds``.
    With ``compact=True`` returns ``1h 3m 5s``.
    """
    total_seconds = max(0, int(delta.total_seconds()))
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    if compact:
        parts: list[str] = []
        if days:
            parts.append(f"{days}d")
        if hours or (days and (minutes or seconds)):
            parts.append(f"{hours}h")
        if minutes or (hours and seconds):
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds or not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return ", ".join(parts)


def format_relative_timestamp(dt: datetime) -> str:
    """Return a relative timestamp marker (``<t:unix:R>``)."""
    return format_timestamp(dt, "R")
