import pytest

from clovord.commands import CommandTree, Interaction


class _FailingHTTP:
    async def post(self, *args, **kwargs):
        return {}

    async def patch(self, *args, **kwargs):
        return {}


@pytest.mark.asyncio
async def test_command_dispatch_recovers_after_handler_failure_before_response() -> None:
    bot = type("Bot", (), {"_logger": None, "http": _FailingHTTP()})()
    tree = CommandTree(bot)

    @tree.command(name="boom", description="fail")
    async def boom(interaction):
        raise RuntimeError("members intent missing")

    sent: list[str] = []

    class _Response:
        is_done = False

        async def send_message(self, content: str = "", **kwargs):
            sent.append(content)

    class _Followup:
        async def send(self, content: str = "", **kwargs):
            sent.append(f"send:{content}")

        async def edit_original(self, content: str = "", **kwargs):
            sent.append(f"edit:{content}")

    original_interaction = Interaction

    def _fake_interaction(bot_obj, payload):
        interaction = original_interaction(bot_obj, payload)
        interaction.response = _Response()
        interaction.followup = _Followup()
        return interaction

    import clovord.commands as commands_module

    commands_module.Interaction = _fake_interaction
    try:
        handled = await tree.dispatch(
            {
                "type": 2,
                "id": "1",
                "token": "token",
                "application_id": "app",
                "data": {"name": "boom"},
            }
        )
    finally:
        commands_module.Interaction = original_interaction

    assert handled is True
    assert sent == ["Command failed: members intent missing"]


@pytest.mark.asyncio
async def test_command_dispatch_recovers_after_handler_failure_after_defer() -> None:
    bot = type("Bot", (), {"_logger": None, "http": _FailingHTTP()})()
    tree = CommandTree(bot)

    @tree.command(name="boom", description="fail after defer")
    async def boom(interaction):
        await interaction.response.defer()
        raise RuntimeError("members intent missing")

    sent: list[str] = []

    class _Response:
        is_done = False

        async def defer(self, **kwargs):
            self.is_done = True

        async def send_message(self, content: str = "", **kwargs):
            sent.append(f"send:{content}")

    class _Followup:
        async def send(self, content: str = "", **kwargs):
            sent.append(f"followup-send:{content}")

        async def edit_original(self, content: str = "", **kwargs):
            sent.append(f"edit:{content}")

    original_interaction = Interaction

    def _fake_interaction(bot_obj, payload):
        interaction = original_interaction(bot_obj, payload)
        response = _Response()
        interaction.response = response
        interaction.followup = _Followup()

        async def _defer(**kwargs):
            interaction._deferred = True
            response.is_done = True

        response.defer = _defer
        return interaction

    import clovord.commands as commands_module

    commands_module.Interaction = _fake_interaction
    try:
        handled = await tree.dispatch(
            {
                "type": 2,
                "id": "1",
                "token": "token",
                "application_id": "app",
                "data": {"name": "boom"},
            }
        )
    finally:
        commands_module.Interaction = original_interaction

    assert handled is True
    assert sent == ["edit:Command failed: members intent missing"]
