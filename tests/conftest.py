from __future__ import annotations

import logging

import pytest


@pytest.fixture(autouse=True)
def _capture_clovord_logs(caplog: pytest.LogCaptureFixture):
    """
    clovord loggers do not propagate to root (so user formatters stay separate).
    Attach pytest's capture handler so existing caplog assertions keep working.
    """
    logger = logging.getLogger("clovord")
    logger.addHandler(caplog.handler)
    try:
        yield
    finally:
        logger.removeHandler(caplog.handler)
