from __future__ import annotations

from typing import Any, Iterable, Sequence


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        if isinstance(data, dict):
            return data
    raise TypeError(f"Component must be a dict or expose to_dict(), got {type(value)!r}")


def serialize_components(components: Sequence[Any] | None) -> list[dict[str, Any]]:
    if not components:
        return []
    return [_as_dict(item) for item in components]


def has_layout_components(components: Sequence[Any] | None) -> bool:
    """True when Components V2 layout nodes are present (container/text/…)."""
    for item in serialize_components(components):
        type_id = int(item.get("type") or 0)
        if type_id in {9, 10, 11, 12, 14, 17}:
            return True
        nested = item.get("components")
        if isinstance(nested, list) and has_layout_components(nested):
            return True
    return False


class Component:
    """Base Components V2 node."""

    type: int = 0

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError


class TextDisplay(Component):
    type = 10

    def __init__(self, content: str) -> None:
        self.content = str(content or "")

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "content": self.content}


class Separator(Component):
    type = 14

    def __init__(self, *, divider: bool | None = None, spacing: int | None = None) -> None:
        self.divider = divider
        self.spacing = spacing

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type}
        if self.divider is not None:
            payload["divider"] = bool(self.divider)
        if self.spacing is not None:
            payload["spacing"] = int(self.spacing)
        return payload


class Container(Component):
    type = 17

    def __init__(
        self,
        *children: Any,
        accent_color: int | None = None,
        spoiler: bool = False,
    ) -> None:
        self.children: list[Any] = list(children)
        self.accent_color = accent_color
        self.spoiler = bool(spoiler)

    def add(self, *children: Any) -> Container:
        self.children.extend(children)
        return self

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "components": serialize_components(self.children),
        }
        if self.accent_color is not None:
            payload["accent_color"] = int(self.accent_color)
        if self.spoiler:
            payload["spoiler"] = True
        return payload


class ActionRow(Component):
    type = 1

    def __init__(self, *children: Any) -> None:
        self.children: list[Any] = list(children)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "components": serialize_components(self.children),
        }


class Button(Component):
    type = 2

    def __init__(
        self,
        *,
        label: str | None = None,
        custom_id: str | None = None,
        style: int = 1,
        url: str | None = None,
        disabled: bool = False,
        emoji: dict[str, Any] | None = None,
    ) -> None:
        self.label = label
        self.custom_id = custom_id
        self.style = int(style)
        self.url = url
        self.disabled = bool(disabled)
        self.emoji = emoji

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type, "style": self.style}
        if self.label is not None:
            payload["label"] = str(self.label)
        if self.custom_id is not None:
            payload["custom_id"] = str(self.custom_id)
        if self.url is not None:
            payload["url"] = str(self.url)
        if self.disabled:
            payload["disabled"] = True
        if self.emoji is not None:
            payload["emoji"] = self.emoji
        return payload


__all__ = [
    "Component",
    "TextDisplay",
    "Separator",
    "Container",
    "ActionRow",
    "Button",
    "serialize_components",
    "has_layout_components",
]
