
from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import pkgutil
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .errors import ClovordExtensionError, ClovordInvalidTokenError
from .events import EventErrorPolicy, EventManager
from .commands import CommandTree
from .models.channel import Channel
from .models.domainlist import DomainlistEntry
from .models.guild import Guild
from .models.user import User
from .utils.payload import unwrap_payload
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
        autoupdate: bool = False,
        event_error_policy: EventErrorPolicy = "log",
    ) -> None:
        self.events = EventManager(error_policy=event_error_policy)
        self.http = HTTPClient()
        self.gateway = GatewayClient(self)
        self.tree = CommandTree(self)
        self._logger = get_logger()
        self._run_task: asyncio.Task[None] | None = None
        self._auto_online_presence = auto_online_presence
        self.autoupdate = bool(autoupdate)
        self._library_autoupdate_started = False
        self._library_update_notice_sent = False
        self._presence_set_explicitly = False
        self._token: str | None = None
        self._is_running = False
        self._intents = Intents.none()
        self._loaded_extensions: dict[str, object] = {}
        self._user: User | None = None
        self._ready_at: datetime | None = None
        self._is_ready = False
        self._guild_ids: tuple[str, ...] = ()
        self._guilds: dict[str, Guild] = {}
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

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def user_id(self) -> str | None:
        if self._user is None:
            return None
        return self._user.id

    @property
    def latency(self) -> float:
        """Gateway heartbeat round-trip latency in seconds.

        Returns ``float('nan')`` until the first HEARTBEAT_ACK is received.
        Typical usage: ``round(bot.latency * 1000)`` for milliseconds.
        """
        return self.gateway.latency

    @property
    def is_ready(self) -> bool:
        """Whether the bot has received READY and is connected to the gateway."""
        return self._is_ready

    @property
    def started_at(self) -> datetime | None:
        """UTC timestamp when the bot last received READY."""
        return self._ready_at

    @property
    def uptime(self) -> timedelta:
        """Elapsed time since the last READY event."""
        if self._ready_at is None:
            return timedelta(0)
        return datetime.now(timezone.utc) - self._ready_at

    @property
    def guild_ids(self) -> tuple[str, ...]:
        """Guild IDs known from the latest READY payload."""
        return self._guild_ids

    @property
    def guilds(self) -> Mapping[str, Guild]:
        """Guild objects cached from READY and guild gateway events."""
        return self._guilds

    def get_guild(self, guild_id: str) -> Guild | None:
        return self._guilds.get(str(guild_id))

    async def fetch_channel(self, channel_id: str) -> Channel:
        """Fetch a channel object from the API."""
        response = await self.http.get(f"/channels/{channel_id}")
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("fetch_channel returned a non-object payload")
        return Channel.from_dict(payload, bot=self)

    async def search_domain(self, domain: str) -> DomainlistEntry | None:
        """Look up a single domain via ``GET /domains/search``.

        Requires ``INTENT_DOMAINLIST_LIMITED`` (exact domain only) or
        ``INTENT_DOMAINLIST`` for full search filters.
        """
        domain_value = str(domain or "").strip()
        if not domain_value:
            raise ValueError("domain must not be empty")

        response = await self.http.get("/domains/search", params={"domain": domain_value})
        entries = DomainlistEntry.from_search_response(response)
        return entries[0] if entries else None

    async def search_domains(
        self,
        *,
        q: str | None = None,
        domain: str | None = None,
        reason: str | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
        hash: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        include_subdomains: bool | None = None,
        include_slugs: bool | None = None,
    ) -> list[DomainlistEntry]:
        """Search the Clovord domainlist via ``GET /domains/search``.

        Full-text and filtered search requires ``INTENT_DOMAINLIST``.
        Bots with only ``INTENT_DOMAINLIST_LIMITED`` may pass ``domain`` alone.
        """
        params: dict[str, Any] = {"offset": int(offset)}
        if q is not None:
            params["q"] = str(q).strip()
        if domain is not None:
            params["domain"] = str(domain).strip()
        if reason is not None:
            params["reason"] = str(reason).strip()
        if status is not None:
            params["status"] = str(status).strip()
        if tags:
            params["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]
        if hash is not None:
            params["hash"] = str(hash).strip()
        if limit is not None:
            params["limit"] = int(limit)
        if include_subdomains is not None:
            params["include_subdomains"] = "true" if include_subdomains else "false"
        if include_slugs is not None:
            params["include_slugs"] = "true" if include_slugs else "false"

        if not any(key in params for key in ("q", "domain", "reason", "status", "tags", "hash")):
            raise ValueError("search_domains requires at least one search parameter")

        response = await self.http.get("/domains/search", params=params)
        return DomainlistEntry.from_search_response(response)

    def _mark_ready(
        self,
        *,
        at: datetime,
        guild_ids: list[str],
        guilds: dict[str, Guild],
    ) -> None:
        self._ready_at = at
        self._is_ready = True
        self._guild_ids = tuple(guild_ids)
        self._guilds = dict(guilds)

    def _mark_disconnected(self) -> None:
        self._is_ready = False

    def _cache_guild(self, guild: Guild) -> None:
        if guild.id:
            self._guilds[guild.id] = guild
            if guild.id not in self._guild_ids:
                self._guild_ids = (*self._guild_ids, guild.id)

    def _remove_guild(self, guild_id: str) -> Guild | None:
        return self._guilds.pop(str(guild_id), None)

    def _set_guild_ids(self, guild_ids: list[str]) -> None:
        self._guild_ids = tuple(str(guild_id) for guild_id in guild_ids)

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
        self._mark_disconnected()

    async def __aenter__(self) -> Bot:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        await self.close()

    async def _handle_gateway_event(self, event_name: str, data_full: Any, data_part: Any) -> None:
        await dispatch_gateway_event(self, event_name, data_full, data_part)
