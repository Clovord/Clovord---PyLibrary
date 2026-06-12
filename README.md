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

<!-- latest-release-notes:start -->
## Latest Release Notes
Version: `0.1.12dev2`
Last commit: feat: update version to 0.1.12dev2

### Added
- update version to 0.1.12dev2
- implement library update event handling with logging
- add webhook notification for clovord.py release process

### Docs
- update for v0.1.12dev1

See full history in CHANGELOG.md.
<!-- latest-release-notes:end -->
