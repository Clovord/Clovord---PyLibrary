from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable


CommandCallback = Callable[..., Awaitable[Any]]


def _unwrap_payload(response: dict[str, Any] | list[Any] | None) -> Any:
    if not isinstance(response, dict):
        return response
    for key in ("data", "payload", "commands"):
        if key in response:
            return response[key]
    return response


class Interaction:
    """Lightweight interaction wrapper for slash-command handlers."""

    def __init__(self, bot: Any, payload: dict[str, Any]) -> None:
        self._bot = bot
        self.raw = payload
        self.id = str(payload.get("id") or "")
        self.token = str(payload.get("token") or "")
        self.type = int(payload.get("type") or 0)
        self.application_id = str(payload.get("application_id") or "")
        self.guild_id = payload.get("guild_id")
        self.channel_id = payload.get("channel_id")
        self.data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        self.user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
        self.member = payload.get("member") if isinstance(payload.get("member"), dict) else None
        self.command_name = str(self.data.get("name") or "")
        self._responded = False

    async def response_send_message(
        self,
        content: str = "",
        *,
        components: list[Any] | None = None,
        ephemeral: bool = False,
    ) -> Any:
        """Respond to this interaction with a channel message (callback type 4)."""
        if self._responded:
            raise RuntimeError("Interaction already responded")
        if not self.id or not self.token:
            raise RuntimeError("Interaction is missing id/token")

        flags = 64 if ephemeral else 0
        body: dict[str, Any] = {
            "type": 4,
            "data": {
                "content": str(content or ""),
                "flags": flags,
            },
        }
        if components is not None:
            body["data"]["components"] = components

        response = await self._bot.http.post(
            f"/interactions/{self.id}/{self.token}/callback",
            json=body,
        )
        self._responded = True
        return _unwrap_payload(response)

    # Discord.py-style alias
    async def send(self, content: str = "", **kwargs: Any) -> Any:
        return await self.response_send_message(content, **kwargs)


class CommandTree:
    """Register and sync application slash commands for the connected bot."""

    def __init__(self, bot: Any) -> None:
        self._bot = bot
        self._pending: list[dict[str, Any]] = []
        self._handlers: dict[str, CommandCallback] = {}

    def command(
        self,
        *,
        name: str,
        description: str = "",
        options: list[dict[str, Any]] | None = None,
        type: int = 1,
        nsfw: bool = False,
        dm_permission: bool = True,
        visibility: dict[str, Any] | None = None,
        guild_id: str | None = None,
    ):
        """Decorator that queues a chat-input command and binds its handler."""

        def decorator(func: CommandCallback):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Slash command handler must be an async function")
            self.add_command(
                name=name,
                description=description,
                options=options,
                type=type,
                nsfw=nsfw,
                dm_permission=dm_permission,
                visibility=visibility,
                guild_id=guild_id,
                callback=func,
            )
            return func

        return decorator

    def add_command(
        self,
        *,
        name: str,
        description: str = "",
        options: list[dict[str, Any]] | None = None,
        type: int = 1,
        nsfw: bool = False,
        dm_permission: bool = True,
        visibility: dict[str, Any] | None = None,
        guild_id: str | None = None,
        callback: CommandCallback | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": int(type),
            "name": str(name),
            "description": str(description or ""),
            "options": list(options or []),
            "nsfw": bool(nsfw),
            "dm_permission": bool(dm_permission),
        }
        if visibility is not None:
            payload["visibility"] = visibility
        if guild_id is not None:
            payload["_guild_id"] = str(guild_id)
        self._pending.append(payload)
        if callback is not None:
            self._handlers[str(name).lower()] = callback
        return payload

    async def dispatch(self, payload: dict[str, Any]) -> bool:
        """Route an INTERACTION_CREATE payload to a registered command handler."""
        if not isinstance(payload, dict):
            return False
        if int(payload.get("type") or 0) != 2:
            return False
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        name = str(data.get("name") or "").strip().lower()
        handler = self._handlers.get(name)
        if handler is None:
            return False
        interaction = Interaction(self._bot, payload)
        await handler(interaction)
        return True

    async def upsert(
        self,
        *,
        name: str,
        description: str = "",
        options: list[dict[str, Any]] | None = None,
        type: int = 1,
        nsfw: bool = False,
        dm_permission: bool = True,
        visibility: dict[str, Any] | None = None,
        guild_id: str | None = None,
        application_id: str | None = None,
    ) -> Any:
        """Create a command, or PATCH an existing one with the same name in scope."""
        app_id = self._resolve_application_id(application_id)
        body: dict[str, Any] = {
            "type": int(type),
            "name": str(name),
            "description": str(description or ""),
            "options": list(options or []),
            "nsfw": bool(nsfw),
            "dm_permission": bool(dm_permission),
        }
        if visibility is not None:
            body["visibility"] = visibility

        existing = await self.fetch(guild_id=guild_id, application_id=app_id)
        rows = existing if isinstance(existing, list) else []
        match = next(
            (row for row in rows if isinstance(row, dict) and str(row.get("name") or "") == str(name)),
            None,
        )
        if match and match.get("id"):
            command_id = match["id"]
            if guild_id:
                path = f"/applications/{app_id}/guilds/{guild_id}/commands/{command_id}"
            else:
                path = f"/applications/{app_id}/commands/{command_id}"
            response = await self._bot.http.patch(path, json=body)
            return _unwrap_payload(response)

        if guild_id:
            path = f"/applications/{app_id}/guilds/{guild_id}/commands"
        else:
            path = f"/applications/{app_id}/commands"

        response = await self._bot.http.post(path, json=body)
        return _unwrap_payload(response)

    async def sync(
        self,
        *,
        guild_id: str | None = None,
        application_id: str | None = None,
        commands: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Bulk overwrite commands for global or guild scope (PUT)."""
        app_id = self._resolve_application_id(application_id)
        source = list(commands) if commands is not None else list(self._pending)

        if guild_id is None:
            scoped = [c for c in source if not c.get("_guild_id")]
            path = f"/applications/{app_id}/commands"
        else:
            gid = str(guild_id)
            scoped = [
                c
                for c in source
                if c.get("_guild_id") is None or str(c.get("_guild_id")) == gid
            ]
            path = f"/applications/{app_id}/guilds/{gid}/commands"

        body = []
        for item in scoped:
            cleaned = {k: v for k, v in item.items() if k != "_guild_id"}
            body.append(cleaned)

        response = await self._bot.http.put(path, json=body)
        return _unwrap_payload(response)

    async def fetch(
        self,
        *,
        guild_id: str | None = None,
        application_id: str | None = None,
    ) -> Any:
        app_id = self._resolve_application_id(application_id)
        if guild_id:
            path = f"/applications/{app_id}/guilds/{guild_id}/commands"
        else:
            path = f"/applications/{app_id}/commands"
        response = await self._bot.http.get(path)
        return _unwrap_payload(response)

    async def delete(
        self,
        command_id: str,
        *,
        guild_id: str | None = None,
        application_id: str | None = None,
    ) -> Any:
        app_id = self._resolve_application_id(application_id)
        if guild_id:
            path = f"/applications/{app_id}/guilds/{guild_id}/commands/{command_id}"
        else:
            path = f"/applications/{app_id}/commands/{command_id}"
        return await self._bot.http.delete(path)

    def clear(self) -> None:
        self._pending.clear()
        self._handlers.clear()

    def _resolve_application_id(self, application_id: str | None) -> str:
        if application_id:
            return str(application_id)
        user_id = getattr(self._bot, "user_id", None)
        if user_id:
            return str(user_id)
        raise RuntimeError(
            "application_id is required until the bot has connected (READY) or pass application_id="
        )
