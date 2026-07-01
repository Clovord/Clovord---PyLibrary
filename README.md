# clovord

A Python SDK for interacting with the Clovord Gateway and REST API.

## Installation

```bash
pip install clovord
```

For local development:

```bash
pip install -e .[dev]
```

## Usage

```python
import clovord
import os
from clovord import Bot
import json


intents = clovord.Intents.default()
intents.members = True
intents.messages = True
intents.presence = True

bot = Bot(intents=intents)

@bot.event
async def on_ready():
    print("READY EVENT FIRED")

@bot.event
async def on_ready_payload(data):
    print("READY PAYLOAD:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

bot.run(os.environ["BOT_TOKEN"])
```

## Overview

- `Bot` is the main entrypoint.
- The Gateway connection is handled internally with heartbeat and reconnect support.
- The REST client is asynchronous and available through `bot.http`.

## Extensions (Cogs-like)

`clovord.py` supports extension modules via `setup(bot)`.

```python
# handlers/message_create.py
def setup(bot):
    @bot.event
    async def on_message(message):
        if message.content.startswith("!"):
            await message.channel.send("Hello from extension")
```

```python
from pathlib import Path
from clovord import Bot

bot = Bot()

# Load one importable module
bot.load_extension("mybot.handlers.message_create")

# Load multiple modules
bot.load_extensions(
    "mybot.handlers.message_create",
    "mybot.handlers.ready",
)

# Load all modules from a package (and subpackages)
bot.load_extensions_from_package("mybot.handlers")

# Load all modules from a folder path (and subfolders)
bot.load_extensions_from_path(Path(__file__).parent / "handlers")
```

<!-- latest-release-notes:start -->
## Latest Release Notes
Version: `0.1.12dev4`
Last commit: Merge branch 'main' of https://github.com/Clovord/Library---py---clovord.py

### Added
- update version to 0.1.12dev4 and enhance logger setup

### Docs
- update for v0.1.12dev3

### Other
- Merge branch 'main' of https://github.com/Clovord/Library---py---clovord.py

See full history in CHANGELOG.md.
<!-- latest-release-notes:end -->
