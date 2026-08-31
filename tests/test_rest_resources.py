from __future__ import annotations

from typing import Any

import pytest

from clovord.bot import Bot
from clovord.commands import Interaction, InteractionFollowup
from clovord.http import HTTPClient
from clovord.models.channel import Channel
from clovord.models.guild import Guild
from clovord.models.message import Message
from clovord.utils.payload import unwrap_payload
from clovord.webhook import Webhook


class _FakeHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def get(self, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("GET", path, {"auth": auth, **kwargs}))
        if path == "/channels/7":
            return {"payload": {"id": "7", "name": "general", "guild_id": "3"}}
        if path == "/channels/7/messages":
            return {
                "payload": {
                    "messages": [
                        {
                            "id": "99",
                            "content": "hello",
                            "channel_id": "7",
                            "author": {"id": "1", "username": "bot"},
                        }
                    ]
                }
            }
        if path == "/guilds/3/members/9":
            return {"payload": {"user": {"id": "9", "username": "member"}, "roles": []}}
        if path == "/guilds/3/roles":
            return {"payload": {"roles": [{"id": "4", "name": "Member"}]}}
        return {"payload": {}}

    async def post(self, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("POST", path, {"auth": auth, **kwargs}))
        if path.endswith("/messages"):
            return {
                "payload": {
                    "id": "100",
                    "content": kwargs.get("json", {}).get("content", ""),
                    "channel_id": "7",
                    "author": {"id": "1", "username": "bot"},
                }
            }
        if path.startswith("/webhooks/") or path.endswith("/followup"):
            return {
                "payload": {
                    "id": "101",
                    "content": kwargs.get("json", {}).get("content", ""),
                    "channel_id": "7",
                    "author": {"id": "1", "username": "bot"},
                }
            }
        return {"payload": {"ok": True}}

    async def patch(self, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("PATCH", path, {"auth": auth, **kwargs}))
        return {
            "payload": {
                "id": "99",
                "content": kwargs.get("json", {}).get("content", "edited"),
                "channel_id": "7",
                "author": {"id": "1", "username": "bot"},
            }
        }

    async def delete(self, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("DELETE", path, {"auth": auth, **kwargs}))
        return {}


@pytest.mark.asyncio
async def test_channel_fetch_send_and_history() -> None:
    bot = Bot()
    bot.http = _FakeHTTP()  # type: ignore[assignment]
    channel = Channel(id="7", _bot=bot)

    fetched = await channel.fetch()
    assert fetched.name == "general"

    message = await channel.send("hello")
    assert isinstance(message, Message)
    assert message.content == "hello"

    history = await channel.history(limit=5)
    assert len(history) == 1
    assert history[0].id == "99"


@pytest.mark.asyncio
async def test_message_edit_and_delete() -> None:
    bot = Bot()
    bot.http = _FakeHTTP()  # type: ignore[assignment]
    message = Message.from_dict(
        {
            "id": "99",
            "content": "hello",
            "channel_id": "7",
            "author": {"id": "1", "username": "bot"},
        },
        bot=bot,
    )

    edited = await message.edit(content="edited")
    assert edited.content == "edited"
    await message.delete()
    assert any(call[0] == "DELETE" for call in bot.http.calls)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_guild_member_and_role_fetch() -> None:
    bot = Bot()
    bot.http = _FakeHTTP()  # type: ignore[assignment]
    guild = Guild(id="3", name="Guild", _bot=bot)

    member = await guild.fetch_member("9")
    assert member.user.username == "member"

    roles = await guild.fetch_roles()
    assert roles[0].name == "Member"


@pytest.mark.asyncio
async def test_interaction_followup_uses_interaction_path() -> None:
    bot = Bot()
    bot.http = _FakeHTTP()  # type: ignore[assignment]
    interaction = Interaction(
        bot,
        {
            "id": "1",
            "token": "token",
            "application_id": "app",
            "type": 2,
            "data": {"name": "ping"},
        },
    )

    message = await interaction.followup.send("pong")
    assert message.content == "pong"
    method, path, kwargs = bot.http.calls[-1]  # type: ignore[attr-defined]
    assert method == "POST"
    assert path == "/interactions/1/token/followup"
    assert kwargs["auth"] is False


def test_webhook_from_url() -> None:
    http = HTTPClient()
    webhook = Webhook.from_url(http, "https://clovord.com/api/v2/webhooks/1/secret")
    assert webhook.id == "1"
    assert webhook.token == "secret"


def test_unwrap_payload_prefers_payload_key() -> None:
    assert unwrap_payload({"payload": {"id": "1"}, "code": "200002"}) == {"id": "1"}
