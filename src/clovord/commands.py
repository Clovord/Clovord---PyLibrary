from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from .ui.components import has_layout_components, serialize_components
from .utils.command_params import bind_interaction_options, extract_command_options, missing_required_parameters
from .utils.payload import unwrap_payload

if TYPE_CHECKING:
    from .models.message import Message


CommandCallback = Callable[..., Awaitable[Any]]

# Message flags
EPHEMERAL = 1 << 6  # 64
IS_COMPONENTS_V2 = 1 << 15  # 32768


class InteractionResponse:
    """Discord.py-style first response helper (`interaction.response`)."""

    def __init__(self, interaction: Interaction) -> None:
        self._interaction = interaction

    @property
    def is_done(self) -> bool:
        return self._interaction._responded

    async def send_message(
        self,
        content: str | None = None,
        *,
        components: list[Any] | None = None,
        ephemeral: bool = False,
        flags: int | None = None,
    ) -> Any:
        """Respond with a channel message (interaction callback type 4)."""
        interaction = self._interaction
        if interaction._responded:
            raise RuntimeError("Interaction has already been responded to")
        if not interaction.id or not interaction.token:
            raise RuntimeError("Interaction is missing id/token")

        serialized = serialize_components(components) if components is not None else None
        text = "" if content is None else str(content)
        if not text and not serialized:
            raise ValueError("send_message requires content and/or components")

        resolved_flags = 0 if flags is None else int(flags)
        if ephemeral:
            resolved_flags |= EPHEMERAL
        if serialized and has_layout_components(serialized):
            resolved_flags |= IS_COMPONENTS_V2

        data: dict[str, Any] = {"flags": resolved_flags}
        if text:
            data["content"] = text
        if serialized is not None:
            data["components"] = serialized

        response = await interaction._bot.http.post(
            f"/interactions/{interaction.id}/{interaction.token}/callback",
            json={"type": 4, "data": data},
        )
        interaction._responded = True
        interaction._deferred = False
        return unwrap_payload(response)

    async def defer(self, *, ephemeral: bool = False) -> Any:
        """Acknowledge with a deferred channel message (type 5)."""
        interaction = self._interaction
        if interaction._responded:
            raise RuntimeError("Interaction has already been responded to")
        if not interaction.id or not interaction.token:
            raise RuntimeError("Interaction is missing id/token")

        data: dict[str, Any] | None = {"flags": EPHEMERAL} if ephemeral else None
        body: dict[str, Any] = {"type": 5}
        if data is not None:
            body["data"] = data

        response = await interaction._bot.http.post(
            f"/interactions/{interaction.id}/{interaction.token}/callback",
            json=body,
        )
        interaction._responded = True
        interaction._deferred = True
        return unwrap_payload(response)


class InteractionFollowup:
    """Send follow-up messages after the initial interaction response."""

    def __init__(self, interaction: Interaction) -> None:
        self._interaction = interaction

    @property
    def _path(self) -> str:
        interaction_id = self._interaction.id
        token = self._interaction.token
        if not interaction_id or not token:
            raise RuntimeError("Interaction is missing id/token")
        return f"/interactions/{interaction_id}/{token}"

    async def send(
        self,
        content: str | None = None,
        *,
        components: list[Any] | None = None,
        ephemeral: bool = False,
        flags: int | None = None,
    ) -> Message:
        from .models.message import Message

        serialized = serialize_components(components) if components is not None else None
        body: dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if serialized is not None:
            body["components"] = serialized
        resolved_flags = 0 if flags is None else int(flags)
        if ephemeral:
            resolved_flags |= EPHEMERAL
        if serialized and has_layout_components(serialized):
            resolved_flags |= IS_COMPONENTS_V2
        if resolved_flags:
            body["flags"] = resolved_flags
        if not body:
            raise ValueError("send requires content and/or components")

        response = await self._interaction._bot.http.post(
            f"{self._path}/followup",
            json=body,
            auth=False,
        )
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("InteractionFollowup.send returned a non-object payload")
        return Message.from_dict(payload, bot=self._interaction._bot)

    async def edit_original(
        self,
        content: str | None = None,
        *,
        components: list[Any] | None = None,
        ephemeral: bool = False,
        flags: int | None = None,
    ) -> Message:
        from .models.message import Message

        serialized = serialize_components(components) if components is not None else None
        body: dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if serialized is not None:
            body["components"] = serialized
        resolved_flags = 0 if flags is None else int(flags)
        if ephemeral:
            resolved_flags |= EPHEMERAL
        if serialized and has_layout_components(serialized):
            resolved_flags |= IS_COMPONENTS_V2
        if resolved_flags:
            body["flags"] = resolved_flags
        if not body:
            raise ValueError("edit_original requires at least one field")

        response = await self._interaction._bot.http.patch(
            f"{self._path}/messages/@original",
            json=body,
            auth=False,
        )
        payload = unwrap_payload(response)
        if not isinstance(payload, dict):
            raise TypeError("InteractionFollowup.edit_original returned a non-object payload")
        return Message.from_dict(payload, bot=self._interaction._bot)

    async def delete_original(self) -> None:
        await self._interaction._bot.http.delete(
            f"{self._path}/messages/@original",
            auth=False,
        )


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
        self._deferred = False
        self.response = InteractionResponse(self)
        self.followup = InteractionFollowup(self)

    async def response_send_message(self, content: str = "", **kwargs: Any) -> Any:
        """Deprecated alias — prefer ``interaction.response.send_message``."""
        return await self.response.send_message(content, **kwargs)

    async def send(self, content: str = "", **kwargs: Any) -> Any:
        """Deprecated alias — prefer ``interaction.response.send_message``."""
        return await self.response.send_message(content, **kwargs)


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
            resolved_options = list(options) if options is not None else extract_command_options(func)
            self.add_command(
                name=name,
                description=description,
                options=resolved_options,
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
        resolved_options = list(options) if options is not None else extract_command_options(callback) if callback else []
        payload: dict[str, Any] = {
            "type": int(type),
            "name": str(name),
            "description": str(description or ""),
            "options": resolved_options,
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
        try:
            missing = missing_required_parameters(data, handler)
            if missing:
                raise ValueError(f"Missing required option(s): {', '.join(missing)}")
            kwargs = bind_interaction_options(data, handler)
            await handler(interaction, **kwargs)
        except Exception as exc:
            await self._recover_interaction_error(interaction, exc)
        return True

    async def _recover_interaction_error(self, interaction: Interaction, exc: Exception) -> None:
        """Ensure failed slash commands still produce a user-visible response."""
        logger = getattr(self._bot, "_logger", None)
        message = f"Command failed: {exc}"
        try:
            if not interaction.response.is_done:
                await interaction.response.send_message(message)
            elif interaction._deferred:
                await interaction.followup.edit_original(message)
            else:
                await interaction.followup.send(message)
        except Exception as recovery_exc:
            if logger is not None:
                logger.exception("Failed to send command error response: %s", recovery_exc)

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
            return unwrap_payload(response)

        if guild_id:
            path = f"/applications/{app_id}/guilds/{guild_id}/commands"
        else:
            path = f"/applications/{app_id}/commands"

        response = await self._bot.http.post(path, json=body)
        return unwrap_payload(response)

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
        return unwrap_payload(response)

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
        return unwrap_payload(response)

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
