from __future__ import annotations

from typing import Any, Sequence


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
        accessory = item.get("accessory")
        if isinstance(accessory, dict) and has_layout_components([accessory]):
            return True
        items = item.get("items")
        if isinstance(items, list) and items:
            return True
    return False


class ButtonStyle:
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


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


class Thumbnail(Component):
    type = 11

    def __init__(self, url: str) -> None:
        self.url = str(url or "").strip()

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "media": {"url": self.url}}


class MediaGalleryItem:
    def __init__(self, url: str) -> None:
        self.url = str(url or "").strip()

    def to_dict(self) -> dict[str, Any]:
        return {"media": {"url": self.url}}


class MediaGallery(Component):
    type = 12

    def __init__(self, *items: str | MediaGalleryItem) -> None:
        self.items: list[MediaGalleryItem] = []
        for item in items:
            if isinstance(item, MediaGalleryItem):
                self.items.append(item)
            else:
                self.items.append(MediaGalleryItem(str(item)))

    def add(self, url: str) -> MediaGallery:
        self.items.append(MediaGalleryItem(url))
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "items": [item.to_dict() for item in self.items],
        }


class Section(Component):
    type = 9

    def __init__(
        self,
        *children: Any,
        accessory: Thumbnail | Button | None = None,
    ) -> None:
        self.children: list[Any] = list(children)
        self.accessory = accessory

    def add(self, *children: Any) -> Section:
        self.children.extend(children)
        return self

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "components": serialize_components(self.children),
        }
        if self.accessory is not None:
            payload["accessory"] = _as_dict(self.accessory)
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


class SelectOption:
    def __init__(
        self,
        *,
        label: str,
        value: str,
        description: str | None = None,
        emoji: dict[str, Any] | None = None,
        default: bool = False,
    ) -> None:
        self.label = str(label)
        self.value = str(value)
        self.description = description
        self.emoji = emoji
        self.default = bool(default)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "label": self.label,
            "value": self.value,
        }
        if self.description is not None:
            payload["description"] = str(self.description)
        if self.emoji is not None:
            payload["emoji"] = self.emoji
        if self.default:
            payload["default"] = True
        return payload


class StringSelect(Component):
    type = 3

    def __init__(
        self,
        *,
        custom_id: str,
        options: Sequence[SelectOption | dict[str, Any]],
        placeholder: str | None = None,
        min_values: int | None = None,
        max_values: int | None = None,
        disabled: bool = False,
    ) -> None:
        self.custom_id = str(custom_id)
        self.options = list(options)
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = bool(disabled)

    def to_dict(self) -> dict[str, Any]:
        serialized_options: list[dict[str, Any]] = []
        for option in self.options:
            if isinstance(option, SelectOption):
                serialized_options.append(option.to_dict())
            elif isinstance(option, dict):
                serialized_options.append(dict(option))
            else:
                raise TypeError("StringSelect options must be SelectOption or dict")

        payload: dict[str, Any] = {
            "type": self.type,
            "custom_id": self.custom_id,
            "options": serialized_options,
        }
        if self.placeholder is not None:
            payload["placeholder"] = str(self.placeholder)
        if self.min_values is not None:
            payload["min_values"] = int(self.min_values)
        if self.max_values is not None:
            payload["max_values"] = int(self.max_values)
        if self.disabled:
            payload["disabled"] = True
        return payload


class Button(Component):
    type = 2

    def __init__(
        self,
        *,
        label: str | None = None,
        custom_id: str | None = None,
        style: int = ButtonStyle.PRIMARY,
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
    "ButtonStyle",
    "Component",
    "TextDisplay",
    "Separator",
    "Thumbnail",
    "MediaGalleryItem",
    "MediaGallery",
    "Section",
    "Container",
    "ActionRow",
    "SelectOption",
    "StringSelect",
    "Button",
    "serialize_components",
    "has_layout_components",
]
