from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import pkgutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .errors import ClovordExtensionError, ClovordInvalidTokenError
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
        self._loaded_extensions: dict[str, object] = {}
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

    @property
    def loaded_extensions(self) -> tuple[str, ...]:
        return tuple(self._loaded_extensions.keys())

    def load_extension(self, module_name: str) -> None:
        module = importlib.import_module(module_name)
        setup = getattr(module, "setup", None)
        if not callable(setup):
            raise ClovordExtensionError(
                f"Extension '{module_name}' must expose a callable setup(bot)"
            )

        setup(self)
        self._loaded_extensions[module_name] = module

    def load_extensions(self, *module_names: str) -> None:
        for module_name in module_names:
            self.load_extension(module_name)

    def load_extensions_from_package(self, package_name: str, *, recursive: bool = True) -> None:
        package = importlib.import_module(package_name)
        package_paths = getattr(package, "__path__", None)
        if package_paths is None:
            raise ClovordExtensionError(
                f"'{package_name}' is not a package. Use load_extension() for modules."
            )

        for module_info in pkgutil.walk_packages(package_paths, f"{package_name}."):
            if module_info.ispkg and not recursive:
                continue

            if module_info.ispkg:
                continue

            self.load_extension(module_info.name)

    def load_extensions_from_path(self, path: str | Path, *, recursive: bool = True) -> None:
        base_path = Path(path).resolve()
        if not base_path.exists() or not base_path.is_dir():
            raise ClovordExtensionError(f"Extension path does not exist: {base_path}")

        pattern = "**/*.py" if recursive else "*.py"
        for index, file_path in enumerate(sorted(base_path.glob(pattern))):
            if file_path.name.startswith("__"):
                continue

            module_name = f"clovord_ext_{index}_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ClovordExtensionError(f"Could not load extension spec: {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            setup = getattr(module, "setup", None)
            if not callable(setup):
                raise ClovordExtensionError(
                    f"Extension file '{file_path}' must expose a callable setup(bot)"
                )

            setup(self)
            self._loaded_extensions[str(file_path)] = module

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
