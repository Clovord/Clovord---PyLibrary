from __future__ import annotations

from types import SimpleNamespace

import pytest

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


def test_http_retry_after_parsing_uses_bounds_and_defaults() -> None:
    client = HTTPClient()

    capped_response = SimpleNamespace(headers={"Retry-After": "120"})
    assert client._get_retry_after_seconds(capped_response) == 30.0

    invalid_response = SimpleNamespace(headers={"Retry-After": "invalid-date"})
    assert client._get_retry_after_seconds(invalid_response) == 1.0
