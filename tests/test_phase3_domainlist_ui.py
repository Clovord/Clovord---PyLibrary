from __future__ import annotations

from typing import Any

import pytest

from clovord.bot import Bot
from clovord.models.domainlist import DomainlistEntry
from clovord.ui import (
    ActionRow,
    Button,
    ButtonStyle,
    Container,
    MediaGallery,
    Section,
    SelectOption,
    Separator,
    StringSelect,
    TextDisplay,
    Thumbnail,
    has_layout_components,
)


class _FakeDomainHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def get(self, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("GET", path, {"auth": auth, **kwargs}))
        params = kwargs.get("params") or {}

        if path == "/domains/search" and params.get("domain") == "evil.test":
            return {
                "items": [
                    {
                        "data": {
                            "domain": "evil.test",
                            "hash": "abc123",
                            "status": "malicious",
                            "score": 95,
                            "flags": 1,
                        }
                    }
                ]
            }

        if path == "/domains/search" and params.get("q") == "test":
            return {
                "items": [
                    {"data": {"domain": "a.test", "status": "clean", "score": 0, "flags": 0}},
                    {"data": {"domain": "b.test", "status": "unknown", "score": 0, "flags": 0}},
                ]
            }

        return {"items": []}


@pytest.mark.asyncio
async def test_search_domain_parses_multi_status_response() -> None:
    bot = Bot()
    bot.http = _FakeDomainHTTP()  # type: ignore[assignment]

    entry = await bot.search_domain("evil.test")
    assert isinstance(entry, DomainlistEntry)
    assert entry.domain == "evil.test"
    assert entry.status == "malicious"
    assert entry.score == 95

    method, path, kwargs = bot.http.calls[0]  # type: ignore[attr-defined]
    assert method == "GET"
    assert path == "/domains/search"
    assert kwargs["params"] == {"domain": "evil.test"}


@pytest.mark.asyncio
async def test_search_domains_with_filters() -> None:
    bot = Bot()
    bot.http = _FakeDomainHTTP()  # type: ignore[assignment]

    entries = await bot.search_domains(q="test", limit=10, status="clean")
    assert len(entries) == 2
    assert entries[0].domain == "a.test"

    _, _, kwargs = bot.http.calls[0]  # type: ignore[attr-defined]
    assert kwargs["params"]["q"] == "test"
    assert kwargs["params"]["limit"] == 10
    assert kwargs["params"]["status"] == "clean"


def test_domainlist_entry_from_search_response() -> None:
    response = {
        "items": [
            {"data": {"domain": "x.test", "status": "clean", "score": 1, "flags": 0}},
            {"payload": {"domain": "y.test", "status": "unknown", "score": 0, "flags": 0}},
        ]
    }
    entries = DomainlistEntry.from_search_response(response)
    assert len(entries) == 2
    assert entries[0].domain == "x.test"
    assert entries[1].domain == "y.test"


def test_domainlist_entry_host_property() -> None:
    entry = DomainlistEntry.from_dict(
        {"domain": "example.com", "subdomain": "api", "status": "clean", "score": 0, "flags": 0}
    )
    assert entry.host == "api.example.com"


def test_string_select_serialization() -> None:
    select = StringSelect(
        custom_id="pick",
        placeholder="Choose one",
        options=[
            SelectOption(label="One", value="1"),
            SelectOption(label="Two", value="2", default=True),
        ],
        min_values=1,
        max_values=1,
    )
    payload = select.to_dict()
    assert payload["type"] == 3
    assert payload["custom_id"] == "pick"
    assert payload["placeholder"] == "Choose one"
    assert len(payload["options"]) == 2
    assert payload["options"][1]["default"] is True


def test_section_with_thumbnail_accessory() -> None:
    section = Section(
        TextDisplay("Hello"),
        accessory=Thumbnail("https://cdn.example/icon.png"),
    )
    payload = section.to_dict()
    assert payload["type"] == 9
    assert payload["components"][0]["type"] == 10
    assert payload["accessory"]["type"] == 11
    assert payload["accessory"]["media"]["url"] == "https://cdn.example/icon.png"


def test_media_gallery_serialization() -> None:
    gallery = MediaGallery("https://cdn.example/a.png", "https://cdn.example/b.png")
    payload = gallery.to_dict()
    assert payload["type"] == 12
    assert len(payload["items"]) == 2
    assert payload["items"][0]["media"]["url"] == "https://cdn.example/a.png"


def test_button_style_and_layout_detection() -> None:
    button = Button(label="Open", style=ButtonStyle.LINK, url="https://clovord.com")
    assert button.to_dict()["style"] == 5

    container = Container(
        Section(TextDisplay("Title"), accessory=Thumbnail("https://cdn.example/x.png")),
        Separator(),
        ActionRow(Button(label="Go", custom_id="go", style=ButtonStyle.PRIMARY)),
    )
    assert has_layout_components([container]) is True
