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
        autoupdate = False

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

    bot = type("_Bot", (), {"_library_update_notice_sent": False, "autoupdate": False})()
    await library_update_check.check_and_notify_library_update(bot)

    assert called["fetch"] is True
    assert called["handle"] is False


@pytest.mark.asyncio
async def test_library_update_gateway_logs_current_and_new_version(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clovord.events import EventManager
    from clovord.gateway.events import library_update

    class _Bot:
        def __init__(self) -> None:
            self.events = EventManager()
            self.autoupdate = False

    bot = _Bot()
    monkeypatch.setattr(library_update, "__version__", "0.1.20")

    with caplog.at_level("INFO"):
        await library_update.handle(
            bot,
            data_part={
                "library": "clovord.py",
                "version": "0.1.21",
                "message": "Release 0.1.21",
                "commit": "abc123",
                "download_url": "https://pypi.org/project/clovord.py/0.1.21/",
            },
        )

    assert any("Current Version: 0.1.20" in record.message for record in caplog.records)
    assert any("New Version: 0.1.21" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_library_update_gateway_skips_when_already_current(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clovord.gateway.events import library_update

    class _Bot:
        autoupdate = False

    monkeypatch.setattr(library_update, "__version__", "0.1.21")

    with caplog.at_level("INFO"):
        await library_update.handle(
            _Bot(),
            data_part={"library": "clovord.py", "version": "0.1.21"},
        )

    assert not any("LIBRARY UPDATE AVAILABLE" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_library_update_skips_non_python_library(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clovord.events import EventManager
    from clovord.gateway.events import library_update

    called = {"autoupdate": False}

    class _Bot:
        def __init__(self) -> None:
            self.events = EventManager()
            self.autoupdate = True

    async def _fake_autoupdate(bot, *, version=None):
        called["autoupdate"] = True
        return True

    monkeypatch.setattr(library_update, "apply_library_autoupdate", _fake_autoupdate)
    monkeypatch.setattr(library_update, "__version__", "0.1.20")

    with caplog.at_level("INFO"):
        await library_update.handle(
            _Bot(),
            data_part={"library": "clovord.js", "version": "9.9.9"},
        )

    assert not any("LIBRARY UPDATE AVAILABLE" in record.message for record in caplog.records)
    assert called["autoupdate"] is False


@pytest.mark.asyncio
async def test_library_update_autoupdate_false_does_not_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from clovord.events import EventManager
    from clovord.gateway.events import library_update

    called = {"autoupdate": False}

    class _Bot:
        def __init__(self) -> None:
            self.events = EventManager()
            self.autoupdate = False

    async def _fake_autoupdate(bot, *, version=None):
        called["autoupdate"] = True
        return True

    monkeypatch.setattr(library_update, "apply_library_autoupdate", _fake_autoupdate)
    monkeypatch.setattr(library_update, "__version__", "0.1.20")

    await library_update.handle(
        _Bot(),
        data_part={"library": "clovord.py", "version": "0.1.21"},
    )

    assert called["autoupdate"] is False


@pytest.mark.asyncio
async def test_library_update_autoupdate_true_triggers_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from clovord.events import EventManager
    from clovord.gateway.events import library_update

    calls: list[str | None] = []

    class _Bot:
        def __init__(self) -> None:
            self.events = EventManager()
            self.autoupdate = True

    async def _fake_autoupdate(bot, *, version=None):
        calls.append(version)
        return True

    monkeypatch.setattr(library_update, "apply_library_autoupdate", _fake_autoupdate)
    monkeypatch.setattr(library_update, "__version__", "0.1.20")

    await library_update.handle(
        _Bot(),
        data_part={"library": "clovord.py", "version": "0.1.21"},
    )

    assert calls == ["0.1.21"]


@pytest.mark.asyncio
async def test_apply_library_autoupdate_runs_pip_and_restarts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from clovord.utils import library_autoupdate

    closed = {"value": False}
    restarted: list[list[str]] = []

    class _Proc:
        returncode = 0

        async def communicate(self):
            return b"ok", b""

    class _Bot:
        _library_autoupdate_started = False
        autoupdate = True

        async def close(self) -> None:
            closed["value"] = True

    async def _fake_exec(*args, **kwargs):
        assert args[1:5] == ("-m", "pip", "install", "--upgrade")
        assert args[5] == "clovord.py==0.1.23"
        return _Proc()

    def _fake_execv(executable, argv):
        restarted.append(list(argv))

    monkeypatch.setattr(library_autoupdate.asyncio, "create_subprocess_exec", _fake_exec)
    monkeypatch.setattr(library_autoupdate.os, "execv", _fake_execv)
    monkeypatch.setattr(library_autoupdate.sys, "argv", ["bot.py", "--flag"])
    monkeypatch.setattr(library_autoupdate.sys, "executable", "python")

    result = await library_autoupdate.apply_library_autoupdate(_Bot(), version="0.1.23")

    assert result is True
    assert closed["value"] is True
    assert restarted == [["python", "bot.py", "--flag"]]


@pytest.mark.asyncio
async def test_apply_library_autoupdate_skips_when_already_started() -> None:
    from clovord.utils.library_autoupdate import apply_library_autoupdate

    class _Bot:
        _library_autoupdate_started = True
        autoupdate = True

    assert await apply_library_autoupdate(_Bot(), version="0.1.23") is False
