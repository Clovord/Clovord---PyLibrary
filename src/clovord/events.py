from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Literal

from .utils.logger import get_logger

EventHandler = Callable[..., Awaitable[None]]
EventErrorPolicy = Literal["log", "raise", "dispatch"]


class EventManager:
    """Registers and dispatches user-defined async event callbacks."""

    def __init__(self, *, error_policy: EventErrorPolicy = "log") -> None:
        self._handlers: dict[str, EventHandler] = {}
        self._logger = get_logger()
        self._error_policy = error_policy

    @property
    def error_policy(self) -> EventErrorPolicy:
        return self._error_policy

    def set_error_policy(self, error_policy: EventErrorPolicy) -> None:
        self._error_policy = error_policy

    def register(self, name: str, handler: EventHandler) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> EventHandler | None:
        return self._handlers.get(name)

    async def dispatch(self, name: str, *args: object, **kwargs: object) -> None:
        handler = self._handlers.get(name)
        if handler is None:
            return

        try:
            await handler(*args, **kwargs)
        except Exception as exc:
            if self._error_policy == "raise":
                raise

            if self._error_policy == "dispatch" and name != "on_error":
                on_error_handler = self._handlers.get("on_error")
                if on_error_handler is not None:
                    try:
                        await on_error_handler(name, exc, args, kwargs)
                        return
                    except Exception as on_error_exc:
                        self._logger.exception(
                            "on_error handler failed for %s: %s",
                            name,
                            on_error_exc,
                        )

            self._logger.exception("Event handler failed for %s: %s", name, exc)
