from __future__ import annotations

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING, Any

import aiohttp
from ..errors import (
    ClovordError,
    ClovordGatewayDisconnectedError,
    ClovordInvalidTokenError,
)
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..bot import Bot


# Clovord gateway opcodes
GATEWAY_OP_HELLO = 0
GATEWAY_OP_HEARTBEAT = 1
GATEWAY_OP_HEARTBEAT_ACK = 2
GATEWAY_OP_IDENTIFY = 3
GATEWAY_OP_CLIENT_EVENT = 5
GATEWAY_OP_DISPATCH = 7
GATEWAY_OP_PONG = 9


class GatewayClient:
    """Handles Clovord gateway connection lifecycle and dispatching."""

    GATEWAY_URL = "wss://gateway.clovord.com"

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._logger = get_logger()
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._seq: int | None = None
        self._heartbeat_interval: float = 30.0
        self._token: str | None = None
        self._closing = False
        self._identify_sent = False

    async def connect(self, token: str) -> None:
        self._token = token
        backoff = 1.0

        while not self._closing:
            try:
                await self._connect_once()
                backoff = 1.0
            except ClovordInvalidTokenError:
                raise
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if isinstance(exc, ClovordError):
                    self._logger.error("%s", exc)
                else:
                    wrapped = ClovordGatewayDisconnectedError(str(exc))
                    self._logger.error("%s", wrapped)

            if self._closing:
                break

            wait_time = min(backoff, 30.0)
            self._logger.info("Reconnecting gateway in %.1fs", wait_time)
            await asyncio.sleep(wait_time)
            backoff = min(backoff * 2, 30.0)

    async def close(self) -> None:
        self._closing = True
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _connect_once(self) -> None:
        if self._token is None:
            raise ClovordError("CLOVORD_GATEWAY_DISCONNECTED", "Gateway token was not provided")

        self._session = aiohttp.ClientSession()
        try:
            async with self._session.ws_connect(self.GATEWAY_URL, heartbeat=None, autoping=True) as ws:
                self._ws = ws
                self._identify_sent = False
                self._logger.info("Connected to gateway")

                async for msg in ws:
                    if msg.type in {aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY}:
                        payload = self._parse_ws_payload(msg)
                        await self._handle_payload(payload)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        ws_error = ws.exception()
                        reason = str(ws_error) if ws_error is not None else "WebSocket returned an error frame"
                        raise ClovordGatewayDisconnectedError(reason)
                    elif msg.type in {aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED}:
                        close_code = ws.close_code
                        detail = self._string_or_none(msg.extra)
                        reason = f"Gateway closed the connection (code={close_code}"
                        if detail:
                            reason = f"{reason}, reason={detail}"
                        reason = f"{reason})"
                        raise ClovordGatewayDisconnectedError(reason)

                close_code = ws.close_code
                raise ClovordGatewayDisconnectedError(
                    f"Gateway connection ended (code={close_code})"
                )
        finally:
            if self._heartbeat_task is not None:
                self._heartbeat_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._heartbeat_task
                self._heartbeat_task = None

            if self._session is not None and not self._session.closed:
                await self._session.close()
            self._session = None
            self._ws = None

    async def _handle_payload(self, payload: dict[str, Any]) -> None:
        op = payload.get("op")
        event_name = payload.get("t")
        data_part_raw = payload.get("d")
        data_part = data_part_raw if isinstance(data_part_raw, dict) else {"value": data_part_raw}
        data_full = dict(payload)
        data_full["d"] = data_part
        seq = payload.get("s")

        if isinstance(seq, int):
            self._seq = seq

        if op == GATEWAY_OP_HELLO:
            await self._handle_hello(data_part)
            return

        if op == GATEWAY_OP_HEARTBEAT:
            await self._send_heartbeat()
            return

        if op in {GATEWAY_OP_HEARTBEAT_ACK, GATEWAY_OP_PONG}:
            return

        if op == GATEWAY_OP_DISPATCH and isinstance(event_name, str):
            if "ERROR" in event_name or self._looks_like_gateway_error_payload(data_part):
                raise self._build_gateway_error_from_payload(payload)

            await self._bot._handle_gateway_event(event_name, data_full, data_part)
            return

    async def _handle_hello(self, data: Any) -> None:
        if isinstance(data, dict) and isinstance(data.get("heartbeat_interval"), (int, float)):
            self._heartbeat_interval = float(data["heartbeat_interval"]) / 1000.0

        if not self._identify_sent:
            await self._identify()
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _identify(self) -> None:
        if self._token is None:
            raise ClovordInvalidTokenError("Token missing during identify")

        intents_list = self._bot.intents.to_gateway_list()
        payload = {
            "op": GATEWAY_OP_IDENTIFY,
            "d": {
                "identify": {
                    "token": self._token,
                    "intents": intents_list,
                    "encoding": "json",
                    "compress": "none",
                }
            },
        }
        self._logger.info("Sending IDENTIFY with intents=%s", intents_list)
        await self._send(payload)
        self._identify_sent = True

    def _parse_ws_payload(self, msg: aiohttp.WSMessage) -> dict[str, Any]:
        raw: str
        if msg.type == aiohttp.WSMsgType.TEXT:
            raw = msg.data
        elif msg.type == aiohttp.WSMsgType.BINARY:
            try:
                raw = msg.data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ClovordGatewayDisconnectedError(
                    "Gateway sent non-utf8 binary payload"
                ) from exc
        else:
            raise ClovordGatewayDisconnectedError(f"Unsupported gateway frame type: {msg.type}")

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ClovordGatewayDisconnectedError("Gateway sent invalid JSON payload") from exc

        if not isinstance(payload, dict):
            raise ClovordGatewayDisconnectedError("Gateway payload is not a JSON object")

        return payload

    async def _heartbeat_loop(self) -> None:
        while not self._closing:
            await asyncio.sleep(self._heartbeat_interval)
            await self._send_heartbeat()

    async def _send_heartbeat(self) -> None:
        await self._send({"op": 1, "d": self._seq})

    async def _send(self, payload: dict[str, Any]) -> None:
        if self._ws is None or self._ws.closed:
            raise ClovordGatewayDisconnectedError("Cannot send payload: gateway is disconnected")
        await self._ws.send_json(payload)

    async def update_presence(
        self,
        status: str = "online",
        custom_status: str | None = None,
        *,
        _from_ready: bool = False,
    ) -> None:
        allowed_statuses = {"online", "idle", "dnd", "offline"}
        normalized_status = status.strip().lower()
        if normalized_status not in allowed_statuses:
            raise ClovordError(
                "CLOVORD_GATEWAY_PRESENCE_INVALID",
                f"Invalid presence status: {status}",
            )

        payload = {
            "op": GATEWAY_OP_CLIENT_EVENT,
            "d": {
                "type": "presence_update",
                "presence": {
                    "status": normalized_status,
                    "custom_status": custom_status,
                },
            },
        }
        if not _from_ready:
            self._bot._presence_set_explicitly = True
        self._logger.info("Sending presence_update status=%s", normalized_status)
        await self._send(payload)

    def _build_gateway_error_from_payload(self, payload: dict[str, Any]) -> ClovordError:
        event_name = payload.get("t")
        data = payload.get("d")
        detail = self._format_gateway_error_detail(payload)

        base_message = "Gateway requested reconnect" if payload.get("op") == 7 else "Gateway reported an error"
        if isinstance(event_name, str) and event_name.strip():
            base_message = f"{base_message}: event={event_name}"

        redacted_payload = self._redact_sensitive_payload(payload)
        response_json = json.dumps(redacted_payload, ensure_ascii=True, separators=(",", ":"))
        full_message = f"{base_message}; details={detail}; gateway_response={response_json}"

        if isinstance(data, dict):
            status = data.get("status")
            if isinstance(status, dict):
                status_code = status.get("code")
                if isinstance(status_code, int):
                    return ClovordError(f"CLOVORD_GATEWAY_{status_code}", full_message)
                if isinstance(status_code, str) and status_code.strip():
                    normalized = status_code.strip().upper().replace("-", "_")
                    code = normalized if normalized.startswith("CLOVORD_") else f"CLOVORD_GATEWAY_{normalized}"
                    return ClovordError(code, full_message)

            remote_code = data.get("code")
            if isinstance(remote_code, str) and remote_code.startswith("CLOVORD_"):
                return ClovordError(remote_code, full_message)
            if isinstance(remote_code, int):
                return ClovordError(f"CLOVORD_GATEWAY_{remote_code}", full_message)

        return ClovordError("CLOVORD_GATEWAY_DISCONNECTED", full_message)

    @staticmethod
    def _string_or_none(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _format_gateway_detail(data: Any) -> str | None:
        if isinstance(data, str) and data.strip():
            return data.strip()

        if isinstance(data, dict):
            ordered_keys = (
                "message",
                "error",
                "reason",
                "code",
                "event",
                "user_id",
                "disconnect",
                "reconnect",
            )
            parts: list[str] = []
            for key in ordered_keys:
                value = data.get(key)
                if value is None:
                    continue
                text = str(value).strip()
                if text:
                    parts.append(f"{key}={text}")

            if parts:
                return ", ".join(parts)

        return None

    @staticmethod
    def _format_gateway_error_detail(payload: dict[str, Any]) -> str:
        data = payload.get("d")
        if not isinstance(data, dict):
            return "no-detail"

        request = data.get("request") if isinstance(data.get("request"), dict) else {}
        status = data.get("status") if isinstance(data.get("status"), dict) else {}
        errors = data.get("errors") if isinstance(data.get("errors"), dict) else {}

        event = request.get("event")
        method = request.get("method")
        request_id = request.get("id")
        status_code = status.get("code")
        status_message = status.get("code_message")
        custom_message = errors.get("custom_message")

        parts = []
        if event is not None:
            parts.append(f"request.event={event}")
        if method is not None:
            parts.append(f"request.method={method}")
        if request_id is not None:
            parts.append(f"request.id={request_id}")
        if status_code is not None:
            parts.append(f"status.code={status_code}")
        if status_message is not None:
            parts.append(f"status.code_message={status_message}")
        if custom_message is not None:
            parts.append(f"errors.custom_message={custom_message}")

        if not parts:
            return "no-detail"
        return ", ".join(parts)

    @staticmethod
    def _looks_like_gateway_error_payload(data: Any) -> bool:
        if not isinstance(data, dict):
            return False

        status = data.get("status")
        request = data.get("request")
        errors = data.get("errors")
        if isinstance(status, dict) and "code" in status:
            return True
        if isinstance(request, dict) and "event" in request:
            return True
        if isinstance(errors, dict) and any(key in errors for key in ("custom_message", "message", "error")):
            return True

        if "code" in data and any(key in data for key in ("message", "error", "reason", "event")):
            return True

        return bool(data.get("disconnect") or data.get("reconnect"))

    @classmethod
    def _redact_sensitive_payload(cls, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                if cls._is_sensitive_key(key):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = cls._redact_sensitive_payload(item)
            return redacted

        if isinstance(value, list):
            return [cls._redact_sensitive_payload(item) for item in value]

        return value

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        normalized = key.strip().lower()
        return normalized in {
            "token",
            "authorization",
            "identify",
            "access_token",
            "refresh_token",
            "api_key",
            "secret",
            "password",
        }
