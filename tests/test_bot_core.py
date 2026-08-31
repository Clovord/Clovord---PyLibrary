from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from clovord.bot import Bot
from clovord.gateway.events.ready import _extract_ready_guilds, handle as ready_handle
from clovord.models.guild import Guild
from clovord.models.member import Member
from clovord.models.message import Message, PartialMessage
from clovord.models.user import User


@pytest.mark.asyncio
async def test_ready_sets_core_bot_state() -> None:
    bot = Bot()

    assert bot.is_ready is False
    assert bot.started_at is None
    assert bot.uptime == timedelta(0)
    assert bot.guild_ids == ()
    assert bot.guilds == {}

    await ready_handle(
        bot,
        data_part={
            "user": {"id": "1", "username": "TestBot"},
            "guild_ids": ["10"],
            "guilds": [{"id": "10", "name": "Clovord HQ"}],
        },
    )

    assert bot.is_ready is True
    assert bot.started_at is not None
    assert bot.uptime >= timedelta(0)
    assert bot.user is not None
    assert bot.user.username == "TestBot"
    assert bot.guild_ids == ("10",)
    assert bot.get_guild("10") is not None
    assert bot.get_guild("10").name == "Clovord HQ"


def test_extract_ready_guilds_merges_ids_and_objects() -> None:
    bot = Bot()
    guild_ids, guilds = _extract_ready_guilds(
        {
            "guild_ids": ["1"],
            "guilds": [
                {"id": "2", "name": "Second"},
                {"id": "1", "name": "First"},
            ],
        },
        bot=bot,
    )

    assert guild_ids == ["1", "2"]
    assert set(guilds) == {"1", "2"}
    assert isinstance(guilds["2"], Guild)


def test_user_model_parses_display_fields() -> None:
    user = User.from_dict(
        {
            "id": "42",
            "username": "clovord",
            "global_name": "Clovord Bot",
            "discriminator": "0001",
            "bot": True,
        }
    )

    assert user.display_name == "Clovord Bot"
    assert user.mention == "<@42>"
    assert user.bot is True


def test_message_and_partial_message_models() -> None:
    bot = Bot()
    message = Message.from_dict(
        {
            "id": "99",
            "content": "hello",
            "channel_id": "7",
            "guild_id": "3",
            "author": {"id": "1", "username": "bot"},
            "timestamp": 1_700_000_000,
        },
        bot=bot,
    )
    partial = PartialMessage.from_dict({"id": "99", "channel_id": "7"})

    assert message.guild_id == "3"
    assert message.channel_id == "7"
    assert message.author.username == "bot"
    assert partial.id == "99"


def test_member_model_supports_guild_member_add_shape() -> None:
    member = Member.from_dict(
        {
            "guild": {"id": "5"},
            "member": {"id": "9", "username": "new-user"},
        },
        guild_id="5",
        user={"id": "9", "username": "new-user"},
    )

    assert member.guild_id == "5"
    assert member.user.username == "new-user"


def test_bot_disconnect_clears_ready_state() -> None:
    bot = Bot()
    bot._mark_ready(
        at=datetime.now(timezone.utc),
        guild_ids=["1"],
        guilds={"1": Guild(id="1", name="Guild", _bot=bot)},
    )

    bot._mark_disconnected()

    assert bot.is_ready is False
    assert bot.started_at is not None
    assert bot.uptime >= timedelta(0)
