# utils/logger.py
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

_BASE_NAME = "clovord"

# Display aliases so the fixed prefix stays short and stable for users.
_LEVEL_ALIASES = {
    "WARNING": "WARN",
}


class ClovordFormatter(logging.Formatter):
    """Fixed ``❱❱ CLV - {ISO} - LEVEL ❱❱`` line format for all library logs."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: ARG002
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _line_prefix(self, record: logging.LogRecord) -> str:
        level = _LEVEL_ALIASES.get(record.levelname, record.levelname)
        return f"❱❱ CLV - {self.formatTime(record)} - {level} ❱❱"

    def _prefix_lines(self, prefix: str, text: str) -> str:
        # Keep a trailing newline as a trailing prefixed empty line only when
        # the original text ended with one meaningful blank content line.
        parts = text.splitlines()
        if not parts:
            return prefix
        return "\n".join(f"{prefix} {part}" if part else prefix for part in parts)

    def format(self, record: logging.LogRecord) -> str:
        prefix = self._line_prefix(record)
        body = record.getMessage()

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            body = f"{body}\n{record.exc_text}" if body else record.exc_text
        if record.stack_info:
            stack = self.formatStack(record.stack_info)
            body = f"{body}\n{stack}" if body else stack

        return self._prefix_lines(prefix, body)


class ClovordStreamHandler(logging.StreamHandler):
    """Stdout handler whose formatter cannot be replaced by bot authors."""

    def __init__(self, stream=None) -> None:
        super().__init__(stream or sys.stdout)
        self._locked_formatter = ClovordFormatter()
        super().setFormatter(self._locked_formatter)

    def setFormatter(self, fmt: logging.Formatter | None) -> None:  # noqa: ARG002
        # Ignore attempts to swap the CLV formatter.
        super().setFormatter(self._locked_formatter)


def _is_pytest_capture_handler(handler: logging.Handler) -> bool:
    # Keep pytest's LogCaptureHandler formatter intact for record.message assertions.
    return type(handler).__name__ == "LogCaptureHandler"


def _ensure_clovord_handler(logger: logging.Logger) -> None:
    """
    Attach a locked CLV handler on the ``clovord`` logger.

    Does not touch the process root logger, so user logs stay separate.
    Any extra handlers on ``clovord`` are forced onto :class:`ClovordFormatter`
    so the prefix stays consistent (pytest capture handlers are left alone).
    """
    has_ours = False
    for handler in list(logger.handlers):
        if isinstance(handler, ClovordStreamHandler):
            has_ours = True
            handler.setFormatter(None)
        elif _is_pytest_capture_handler(handler):
            continue
        else:
            handler.setFormatter(ClovordFormatter())

    if not has_ours:
        logger.addHandler(ClovordStreamHandler(sys.stdout))

    logger.setLevel(logging.INFO)
    # Keep CLV lines off the root logger so they do not mix with app formatters.
    logger.propagate = False


def get_logger(suffix: str | None = None) -> logging.Logger:
    """
    Return a library logger:

    - ``clovord`` when ``suffix`` is omitted
    - ``clovord.<suffix>`` when set

    Output always uses the fixed ``❱❱ CLV - …`` prefix.
    """
    base = logging.getLogger(_BASE_NAME)
    _ensure_clovord_handler(base)

    if not suffix:
        return base

    child = logging.getLogger(f"{_BASE_NAME}.{suffix}")
    child.setLevel(logging.INFO)
    child.propagate = True
    return child


logger = get_logger()
