from __future__ import annotations

from types import SimpleNamespace

import pytest

from clovord.errors import ClovordError
from clovord.gateway.events.presence_update import _build_presence_states
from clovord.gateway.handler import GatewayClient
from clovord.http import HTTPClient
from clovord.intents import Intents


class _DummyBot:
    def __init__(self) -> None:
        self.intents = Intents.none()
        self._presence_set_explicitly = False


def test_intents_to_gateway_list_serialization() -> None:
    intents = Intents.none()
    intents.presence = True
    intents.members = True

    serialized = intents.to_gateway_list()

    assert "INTENT_PRESENCE" in serialized
    assert "INTENT_GUILD_MEMBERS" in serialized


def test_presence_update_state_builds_backward_compatible_payload() -> None:
    data = {
        "user": {"id": "42", "name": "clovord"},
        "presence": {"status": "idle", "custom_status": "brb"},
    }

    before_state, after_state = _build_presence_states(data)

    assert before_state["user"]["id"] == "42"
    assert after_state["status"] == "idle"
    assert after_state["custom_status"] == "brb"
    assert after_state["user"]["username"] == "clovord"


@pytest.mark.asyncio
async def test_gateway_send_heartbeat_records_timestamp_and_ack_sets_latency() -> None:
    import math

    bot = _DummyBot()
    gateway = GatewayClient(bot)
    sent: list[dict[str, object]] = []

    async def _fake_send(payload: dict[str, object]) -> None:
        sent.append(payload)

    gateway._send = _fake_send  # type: ignore[method-assign]

    assert math.isnan(gateway.latency)
    await gateway._send_heartbeat()
    assert gateway._last_heartbeat is not None
    assert sent and sent[0]["op"] == 1

    gateway._ack_heartbeat()
    assert gateway._last_heartbeat is None
    assert gateway.latency >= 0.0
    assert not math.isnan(gateway.latency)


@pytest.mark.asyncio
async def test_gateway_update_presence_normalizes_status_and_marks_explicit() -> None:
    bot = _DummyBot()
    gateway = GatewayClient(bot)
    captured: dict[str, object] = {}

    async def _fake_send(payload: dict[str, object]) -> None:
        captured["payload"] = payload

    gateway._send = _fake_send  # type: ignore[method-assign]

    await gateway.update_presence("IDLE", custom_status="syncing")

    assert bot._presence_set_explicitly is True
    payload = captured["payload"]
    assert isinstance(payload, dict)
    presence = payload["d"]["presence"]  # type: ignore[index]
    assert presence["status"] == "idle"  # type: ignore[index]


def test_gateway_error_payload_is_redacted_in_exception_message() -> None:
    gateway = GatewayClient(_DummyBot())
    payload = {
        "op": 7,
        "t": "ERROR",
        "d": {
            "status": {"code": 4001, "code_message": "invalid"},
            "request": {"event": "IDENTIFY", "id": "abc"},
            "identify": {"token": "super-secret"},
            "token": "super-secret",
        },
    }

    err = gateway._build_gateway_error_from_payload(payload)
    message = str(err)

    assert err.code == "CLOVORD_GATEWAY_4001"
    assert "super-secret" not in message
    assert "[REDACTED]" in message


@pytest.mark.asyncio
async def test_gateway_error_event_is_dispatched_without_reconnect() -> None:
    handled: list[str] = []

    class _EventBot(_DummyBot):
        async def _handle_gateway_event(self, event_name: str, data_full: object, data_part: object) -> None:
            handled.append(event_name)

    gateway = GatewayClient(_EventBot())
    await gateway._handle_payload(
        {
            "op": 7,
            "t": "GATEWAY_ERROR",
            "d": {
                "status": {"code": 423019, "code_message": "You need the DOMAINLIST_INTENT"},
                "request": {"event": "IDENTIFY"},
                "errors": {"custom_message": "intent not permitted"},
            },
        }
    )

    assert handled == ["GATEWAY_ERROR"]


@pytest.mark.asyncio
async def test_gateway_error_with_disconnect_is_dispatched_then_raised() -> None:
    handled: list[str] = []

    class _EventBot(_DummyBot):
        async def _handle_gateway_event(self, event_name: str, data_full: object, data_part: object) -> None:
            handled.append(event_name)

    gateway = GatewayClient(_EventBot())
    with pytest.raises(ClovordError, match="Gateway requested disconnect"):
        await gateway._handle_payload(
            {
                "op": 7,
                "t": "GATEWAY_ERROR",
                "d": {
                    "status": {"code": 401006, "code_message": "Identify timeout"},
                    "request": {"event": "GATEWAY_IDENTIFY"},
                    "disconnect": True,
                },
            }
        )

    assert handled == ["GATEWAY_ERROR"]


@pytest.mark.asyncio
async def test_gateway_error_with_reconnect_false_forbids_reconnect() -> None:
    class _EventBot(_DummyBot):
        async def _handle_gateway_event(self, event_name: str, data_full: object, data_part: object) -> None:
            return None

    gateway = GatewayClient(_EventBot())
    with pytest.raises(ClovordError, match="Gateway requested disconnect"):
        await gateway._handle_payload(
            {
                "op": 7,
                "t": "GATEWAY_ERROR",
                "d": {
                    "status": {"code": 423006, "code_message": "Account disabled"},
                    "request": {"event": "GATEWAY_IDENTIFY"},
                    "disconnect": True,
                    "reconnect": False,
                },
            }
        )

    assert gateway._reconnect_forbidden is True


def test_no_reconnect_close_code_detection() -> None:
    assert GatewayClient._is_no_reconnect_close_code(4100) is True
    assert GatewayClient._is_no_reconnect_close_code(4199) is True
    assert GatewayClient._is_no_reconnect_close_code(4000) is False
    assert GatewayClient._is_no_reconnect_close_code(4230) is False


@pytest.mark.asyncio
async def test_domainlist_dispatch_is_not_treated_as_gateway_error() -> None:
    handled: list[tuple[str, object]] = []

    class _EventBot(_DummyBot):
        async def _handle_gateway_event(self, event_name: str, data_full: object, data_part: object) -> None:
            handled.append((event_name, data_part))

    gateway = GatewayClient(_EventBot())
    entry = {"id": "1", "domain": "example.com"}
    await gateway._handle_payload(
        {
            "op": 7,
            "t": "DOMAINLIST_ENTRY_CREATE",
            "d": {"entry": entry},
        }
    )

    assert handled == [("DOMAINLIST_ENTRY_CREATE", {"entry": entry})]


@pytest.mark.asyncio
async def test_ready_logs_denied_intents(caplog: pytest.LogCaptureFixture) -> None:
    from clovord.events import EventManager
    from clovord.gateway.events.ready import handle as handle_ready
    from clovord.utils.logger import get_logger

    class _ReadyBot(_DummyBot):
        def __init__(self) -> None:
            super().__init__()
            self.events = EventManager()
            self._logger = get_logger()
            self._auto_online_presence = False
            self._user = None

        @property
        def user(self):
            return self._user

    bot = _ReadyBot()
    with caplog.at_level("ERROR"):
        await handle_ready(
            bot,
            None,
            {
                "user": {"id": "1", "username": "testbot"},
                "intents": {
                    "requested": ["INTENT_DOMAINLIST", "INTENT_PRESENCE"],
                    "granted": {"INTENT_PRESENCE": "full"},
                    "denied": ["INTENT_DOMAINLIST"],
                    "invalid": [],
                },
            },
        )

    assert any("Intent not permitted: INTENT_DOMAINLIST" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_domainlist_entry_create_unwraps_entry() -> None:
    from clovord.events import EventManager
    from clovord.gateway.events.domainlist_entry_create import handle as handle_create

    received: list[object] = []

    class _EventBot(_DummyBot):
        def __init__(self) -> None:
            super().__init__()
            self.events = EventManager()

            async def on_domainlist_entry_create(entry: object) -> None:
                received.append(entry)

            self.events.register("on_domainlist_entry_create", on_domainlist_entry_create)

    entry = {"id": "1", "domain": "example.com"}
    await handle_create(_EventBot(), None, {"entry": entry})
    assert received == [entry]


def test_http_retry_after_parsing_uses_bounds_and_defaults() -> None:
    client = HTTPClient()

    capped_response = SimpleNamespace(headers={"Retry-After": "120"})
    assert client._get_retry_after_seconds(capped_response) == 30.0

    invalid_response = SimpleNamespace(headers={"Retry-After": "invalid-date"})
    assert client._get_retry_after_seconds(invalid_response) == 1.0
