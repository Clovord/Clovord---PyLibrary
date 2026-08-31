from __future__ import annotations

from datetime import timedelta

from clovord.utils.time import format_relative_timestamp, format_timestamp, format_uptime


def test_format_uptime_human_readable() -> None:
    assert format_uptime(timedelta(seconds=26)) == "26 seconds"
    assert format_uptime(timedelta(hours=1, minutes=3, seconds=5)) == "1 hour, 3 minutes, 5 seconds"
    assert format_uptime(timedelta(days=2, hours=1)) == "2 days, 1 hour"


def test_format_uptime_compact() -> None:
    assert format_uptime(timedelta(hours=1, minutes=3, seconds=5), compact=True) == "1h 3m 5s"


def test_format_uptime_strips_microseconds() -> None:
    assert format_uptime(timedelta(seconds=26, microseconds=349582)) == "26 seconds"


def test_format_relative_timestamp() -> None:
    from datetime import datetime, timezone

    marker = format_relative_timestamp(datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert marker == "<t:1704067200:R>"


def test_format_timestamp_styles() -> None:
    from datetime import datetime, timezone

    dt = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)
    assert format_timestamp(dt, "F") == "<t:1704112200:F>"
    assert format_timestamp(dt, "t") == "<t:1704112200:t>"
