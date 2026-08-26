from __future__ import annotations

import logging
from datetime import datetime, timezone
from io import StringIO

from clovord.utils.logger import (
    ClovordFormatter,
    ClovordStreamHandler,
    get_logger,
)


def test_clovord_formatter_uses_fixed_prefix_and_iso_utc() -> None:
    formatter = ClovordFormatter()
    record = logging.LogRecord(
        name="clovord",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="connected",
        args=(),
        exc_info=None,
    )
    record.created = datetime(2026, 8, 26, 18, 30, 45, 123000, tzinfo=timezone.utc).timestamp()

    line = formatter.format(record)
    assert line.startswith("❱❱ CLV - 2026-08-26T18:30:45.123Z - INFO ❱❱ ")
    assert line.endswith("connected")


def test_clovord_formatter_maps_warning_to_warn() -> None:
    formatter = ClovordFormatter()
    record = logging.LogRecord(
        name="clovord",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="slow reconnect",
        args=(),
        exc_info=None,
    )
    record.created = datetime(2026, 8, 26, 18, 30, 45, tzinfo=timezone.utc).timestamp()

    line = formatter.format(record)
    assert " - WARN ❱❱ slow reconnect" in line
    assert "WARNING" not in line


def test_stream_handler_formatter_is_locked() -> None:
    stream = StringIO()
    handler = ClovordStreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger("clovord.test_locked_handler")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("hello-clv")
    output = stream.getvalue().strip()
    assert output.startswith("❱❱ CLV - ")
    assert " - INFO ❱❱ hello-clv" in output


def test_clovord_formatter_prefixes_every_newline() -> None:
    formatter = ClovordFormatter()
    record = logging.LogRecord(
        name="clovord.LibraryUpdater",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=(
            "=== LIBRARY UPDATE AVAILABLE ===\n"
            "Library: clovord.py\n"
            "Current Version: 0.1.20\n"
            "New Version: 0.1.21\n"
            "================================"
        ),
        args=(),
        exc_info=None,
    )
    record.created = datetime(2026, 8, 26, 18, 30, 45, 123000, tzinfo=timezone.utc).timestamp()

    output = formatter.format(record)
    lines = output.splitlines()
    assert len(lines) == 5
    prefix = "❱❱ CLV - 2026-08-26T18:30:45.123Z - INFO ❱❱"
    assert all(line.startswith(prefix) for line in lines)
    assert lines[0] == f"{prefix} === LIBRARY UPDATE AVAILABLE ==="
    assert lines[1] == f"{prefix} Library: clovord.py"
    assert lines[-1] == f"{prefix} ================================"


def test_clovord_formatter_prefixes_exception_lines() -> None:
    import sys

    formatter = ClovordFormatter()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.LogRecord(
            name="clovord",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="handler failed",
            args=(),
            exc_info=sys.exc_info(),
        )
        record.created = datetime(2026, 8, 26, 18, 30, 45, tzinfo=timezone.utc).timestamp()
        output = formatter.format(record)

    lines = output.splitlines()
    assert len(lines) >= 2
    prefix = "❱❱ CLV - 2026-08-26T18:30:45.000Z - ERROR ❱❱"
    assert all(line.startswith(prefix) for line in lines)
    assert lines[0] == f"{prefix} handler failed"


def test_get_logger_does_not_attach_to_root() -> None:
    root_before = list(logging.getLogger().handlers)
    lg = get_logger("PrefixCheck")
    lg.info("ping")
    root_after = list(logging.getLogger().handlers)
    assert root_after == root_before
    assert lg.name == "clovord.PrefixCheck"
    assert logging.getLogger("clovord").propagate is False
