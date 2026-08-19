from __future__ import annotations

import pytest

from clovord.utils.pypi import is_version_outdated, parse_version


def test_parse_version_handles_stable_and_dev_suffixes() -> None:
    assert parse_version("0.1.18") == (0, 1, 18)
    assert parse_version("0.1.13dev4") == (0, 1, 13)


def test_is_version_outdated() -> None:
    assert is_version_outdated("0.1.17", "0.1.18") is True
    assert is_version_outdated("0.1.18", "0.1.18") is False
    assert is_version_outdated("0.1.19", "0.1.18") is False
    assert is_version_outdated("0.1.13dev4", "0.1.13") is False


@pytest.mark.asyncio
async def test_check_and_notify_library_update_sends_notice_when_outdated(monkeypatch: pytest.MonkeyPatch) -> None:
    from clovord.utils import library_update_check

    handled: list[dict] = []

    class _Bot:
        _library_update_notice_sent = False

    async def _fake_fetch(package: str, **kwargs):
        assert package == "clovord.py"
        return "9.9.9"

    async def _fake_handle(bot, data_part=None, data_full=None):
        handled.append(dict(data_part or {}))

    monkeypatch.setattr(library_update_check, "_installed_version", lambda: "0.1.18")
    monkeypatch.setattr(library_update_check, "fetch_pypi_latest_version", _fake_fetch)
    monkeypatch.setattr(library_update_check.library_update, "handle", _fake_handle)

    bot = _Bot()
    await library_update_check.check_and_notify_library_update(bot)

    assert bot._library_update_notice_sent is True
    assert handled[0]["version"] == "9.9.9"
    assert handled[0]["current_version"] == "0.1.18"
    assert handled[0]["source"] == "pypi"


@pytest.mark.asyncio
async def test_check_and_notify_library_update_skips_when_current(monkeypatch: pytest.MonkeyPatch) -> None:
    from clovord.utils import library_update_check

    called = {"fetch": False, "handle": False}

    async def _fake_fetch(package: str, **kwargs):
        called["fetch"] = True
        return "0.1.18"

    async def _fake_handle(bot, data_part=None, data_full=None):
        called["handle"] = True

    monkeypatch.setattr(library_update_check, "_installed_version", lambda: "0.1.18")
    monkeypatch.setattr(library_update_check, "fetch_pypi_latest_version", _fake_fetch)
    monkeypatch.setattr(library_update_check.library_update, "handle", _fake_handle)

    bot = type("_Bot", (), {"_library_update_notice_sent": False})()
    await library_update_check.check_and_notify_library_update(bot)

    assert called["fetch"] is True
    assert called["handle"] is False
