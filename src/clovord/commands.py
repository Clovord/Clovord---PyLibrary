from __future__ import annotations

from typing import Any


def _unwrap_payload(response: dict[str, Any] | list[Any] | None) -> Any:
    if not isinstance(response, dict):
        return response
    for key in ("data", "payload", "commands"):
        if key in response:
            return response[key]
    return response


class CommandTree:
    """Register and sync application slash commands for the connected bot."""

    def __init__(self, bot: Any) -> None:
        self._bot = bot
        self._pending: list[dict[str, Any]] = []

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
        """Decorator that queues a chat-input command for later sync."""

        def decorator(func):
            self.add_command(
                name=name,
                description=description,
                options=options,
                type=type,
                nsfw=nsfw,
                dm_permission=dm_permission,
                visibility=visibility,
                guild_id=guild_id,
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
        return payload

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

    def _resolve_application_id(self, application_id: str | None) -> str:
        if application_id:
            return str(application_id)
        user_id = getattr(self._bot, "user_id", None)
        if user_id:
            return str(user_id)
        raise RuntimeError(
            "application_id is required until the bot has connected (READY) or pass application_id="
        )
