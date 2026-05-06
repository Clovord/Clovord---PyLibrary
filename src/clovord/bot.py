from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from .errors import ClovordInvalidTokenError
from .events import EventErrorPolicy, EventManager
from .gateway.events.dispatcher import dispatch_gateway_event
from .gateway.handler import GatewayClient
from .http import HTTPClient
from .intents import Intents
from .utils.logger import get_logger


EventCallback = Callable[..., Awaitable[None]]


class Bot:
    """Main SDK entrypoint for gateway and API interactions."""

    def __init__(
        self,
        *,
        intents: Intents | int | None = None,
        auto_online_presence: bool = True,
        event_error_policy: EventErrorPolicy = "log",
    ) -> None:
        self.events = EventManager(error_policy=event_error_policy)
        self.http = HTTPClient()
        self.gateway = GatewayClient(self)
        self._logger = get_logger()
        self._run_task: asyncio.Task[None] | None = None
        self._auto_online_presence = auto_online_presence
        self._presence_set_explicitly = False
        self._token: str | None = None
        self._is_running = False
        self._intents = Intents.none()
        self.set_intents(Intents.none() if intents is None else intents)

    @property
    def intents(self) -> Intents:
        return self._intents

    @intents.setter
    def intents(self, intents: Intents | int) -> None:
        self.set_intents(intents)

    def set_intents(self, intents: Intents | int) -> None:
        if isinstance(intents, Intents):
            self._intents = intents
            return

        if isinstance(intents, int):
            self._intents = Intents(intents)
            return

        raise TypeError("intents must be an Intents instance or integer bitmask")

    def event(self, callback: EventCallback) -> EventCallback:
        if not inspect.iscoroutinefunction(callback):
            raise TypeError("Event callback must be an async function")

        self.events.register(callback.__name__, callback)
        return callback

    async def start(self, token: str) -> None:
        token = token.strip()
        if not token:
            raise ClovordInvalidTokenError("Token cannot be empty")

        self._token = token
        await self.http.start(token)
        self._is_running = True

        try:
            await self.gateway.connect(token)
        finally:
            self._is_running = False
            await self.http.close()

    def run(self, token: str) -> asyncio.Task[None] | None:
        """Start the bot and manage the event loop automatically."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.start(token))
            return None

        task = loop.create_task(self.start(token))
        self._run_task = task

        def _on_done(done_task: asyncio.Task[None]) -> None:
            if self._run_task is done_task:
                self._run_task = None
            if done_task.cancelled():
                return

            try:
                exc = done_task.exception()
            except asyncio.CancelledError:
                return

            if exc is not None:
                self._logger.exception("Bot run task failed", exc_info=exc)

        task.add_done_callback(_on_done)
        return task

    async def close(self) -> None:
        await self.gateway.close()
        await self.http.close()
        self._is_running = False

    async def _handle_gateway_event(self, event_name: str, data_full: Any, data_part: Any) -> None:
        await dispatch_gateway_event(self, event_name, data_full, data_part)
