from __future__ import annotations

import pytest

from clovord.commands import CommandTree
from clovord.utils.command_params import bind_interaction_options, extract_command_options, missing_required_parameters


def test_extract_command_options_from_signature() -> None:
    async def handler(interaction, domain: str, limit: int = 10):
        return None

    options = extract_command_options(handler)
    assert len(options) == 2
    assert options[0] == {
        "type": 3,
        "name": "domain",
        "description": "Domain",
        "required": True,
    }
    assert options[1] == {
        "type": 4,
        "name": "limit",
        "description": "Limit",
        "required": False,
    }


def test_bind_interaction_options_coerces_types() -> None:
    async def handler(interaction, domain: str, limit: int = 5):
        return None

    bound = bind_interaction_options(
        {
            "name": "lookup",
            "options": [
                {"name": "domain", "type": 3, "value": "evil.test"},
                {"name": "limit", "type": 4, "value": "12"},
            ],
        },
        handler,
    )
    assert bound == {"domain": "evil.test", "limit": 12}


def test_missing_required_parameters() -> None:
    async def handler(interaction, domain: str, limit: int = 5):
        return None

    missing = missing_required_parameters(
        {"name": "lookup", "options": []},
        handler,
    )
    assert missing == ["domain"]


@pytest.mark.asyncio
async def test_command_decorator_registers_signature_options() -> None:
    bot = object()
    tree = CommandTree(bot)

    @tree.command(name="lookup", description="lookup a domain")
    async def lookup_command(interaction, domain: str):
        await interaction.response.send_message(domain)

    assert len(tree._pending) == 1
    assert tree._pending[0]["options"] == [
        {
            "type": 3,
            "name": "domain",
            "description": "Domain",
            "required": True,
        }
    ]


@pytest.mark.asyncio
async def test_command_dispatch_passes_bound_options() -> None:
    bot = object()
    tree = CommandTree(bot)
    received: dict[str, object] = {}

    @tree.command(name="lookup", description="lookup a domain")
    async def lookup_command(interaction, domain: str):
        received["domain"] = domain
        await interaction.response.send_message(domain)

    class _FakeResponse:
        is_done = False

        async def send_message(self, content: str, **kwargs: object) -> None:
            received["content"] = content

    class _FakeInteraction:
        def __init__(self) -> None:
            self.response = _FakeResponse()
            self._deferred = False

    import clovord.commands as commands_module

    original_interaction = commands_module.Interaction
    commands_module.Interaction = lambda _bot, _payload: _FakeInteraction()  # type: ignore[misc, assignment]
    try:
        handled = await tree.dispatch(
            {
                "type": 2,
                "data": {
                    "name": "lookup",
                    "options": [{"name": "domain", "type": 3, "value": "evil.test"}],
                },
            }
        )
    finally:
        commands_module.Interaction = original_interaction

    assert handled is True
    assert received["domain"] == "evil.test"
    assert received["content"] == "evil.test"
