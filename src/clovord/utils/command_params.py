from __future__ import annotations

import inspect
import types
import typing
from typing import Any, Callable, get_args, get_origin

# Discord-compatible application command option types.
OPTION_SUB_COMMAND = 1
OPTION_SUB_COMMAND_GROUP = 2
OPTION_STRING = 3
OPTION_INTEGER = 4
OPTION_BOOLEAN = 5
OPTION_NUMBER = 10

_PYTHON_TO_OPTION_TYPE: dict[type[Any], int] = {
    str: OPTION_STRING,
    int: OPTION_INTEGER,
    bool: OPTION_BOOLEAN,
    float: OPTION_NUMBER,
}

_INTERACTION_PARAM_NAMES = frozenset({"interaction", "inter", "ctx", "context"})


def _resolve_annotation(annotation: Any) -> type[Any]:
    if annotation is inspect.Parameter.empty:
        return str

    if isinstance(annotation, str):
        simple_types = {
            "str": str,
            "int": int,
            "bool": bool,
            "float": float,
        }
        return simple_types.get(annotation, str)

    origin = get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if args:
            return _resolve_annotation(args[0])
        return str

    if isinstance(annotation, type):
        return annotation
    return str


def _parameter_annotations(callback: Callable[..., Any]) -> dict[str, Any]:
    try:
        return typing.get_type_hints(callback)
    except Exception:
        return {}


def _option_type_for(annotation: Any) -> int:
    resolved = _resolve_annotation(annotation)
    return _PYTHON_TO_OPTION_TYPE.get(resolved, OPTION_STRING)


def _is_interaction_parameter(param: inspect.Parameter, hints: dict[str, Any]) -> bool:
    if param.name.lower() in _INTERACTION_PARAM_NAMES:
        return True
    annotation = hints.get(param.name, param.annotation)
    resolved = _resolve_annotation(annotation)
    return resolved.__name__ == "Interaction"


def _parameter_description(name: str) -> str:
    return name.replace("_", " ").strip().capitalize() or name


def extract_command_options(callback: Callable[..., Any]) -> list[dict[str, Any]]:
    """Build slash-command option definitions from a handler signature."""
    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        return []

    options: list[dict[str, Any]] = []
    hints = _parameter_annotations(callback)
    for param in signature.parameters.values():
        if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            continue
        if _is_interaction_parameter(param, hints):
            continue

        annotation = hints.get(param.name, param.annotation)
        option: dict[str, Any] = {
            "type": _option_type_for(annotation),
            "name": str(param.name).lower(),
            "description": _parameter_description(str(param.name)),
            "required": param.default is inspect.Parameter.empty,
        }
        options.append(option)
    return options


def _flatten_option_values(options: list[Any] | None) -> dict[str, Any]:
    """Flatten interaction option payloads, including nested subcommands."""
    values: dict[str, Any] = {}
    for item in options or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        opt_type = int(item.get("type") or 0)
        if opt_type in {OPTION_SUB_COMMAND, OPTION_SUB_COMMAND_GROUP}:
            values.update(_flatten_option_values(item.get("options")))
            values["_subcommand"] = name
            continue
        if "value" in item:
            values[name] = item.get("value")
    return values


def _coerce_option_value(value: Any, annotation: Any) -> Any:
    if value is None:
        return None
    resolved = _resolve_annotation(annotation)
    if resolved is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return bool(value)
    if resolved is int:
        return int(value)
    if resolved is float:
        return float(value)
    return str(value)


def bind_interaction_options(
    data: dict[str, Any] | None,
    callback: Callable[..., Any],
) -> dict[str, Any]:
    """Map interaction option values onto handler keyword arguments."""
    if not isinstance(data, dict):
        data = {}

    values = _flatten_option_values(data.get("options") if isinstance(data.get("options"), list) else [])
    bound: dict[str, Any] = {}
    hints = _parameter_annotations(callback)

    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        return bound

    for param in signature.parameters.values():
        if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            continue
        if _is_interaction_parameter(param, hints):
            continue

        key = str(param.name).lower()
        if key not in values:
            if param.default is not inspect.Parameter.empty:
                bound[param.name] = param.default
            continue

        annotation = hints.get(param.name, param.annotation)
        bound[param.name] = _coerce_option_value(values[key], annotation)

    return bound


def missing_required_parameters(
    data: dict[str, Any] | None,
    callback: Callable[..., Any],
) -> list[str]:
    """Return handler parameter names that are required but missing from the interaction."""
    if not isinstance(data, dict):
        data = {}

    values = _flatten_option_values(data.get("options") if isinstance(data.get("options"), list) else [])
    missing: list[str] = []

    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        return missing

    hints = _parameter_annotations(callback)
    for param in signature.parameters.values():
        if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            continue
        if _is_interaction_parameter(param, hints):
            continue
        if param.default is not inspect.Parameter.empty:
            continue
        key = str(param.name).lower()
        if key not in values:
            missing.append(param.name)
    return missing


__all__ = [
    "OPTION_SUB_COMMAND",
    "OPTION_SUB_COMMAND_GROUP",
    "OPTION_STRING",
    "OPTION_INTEGER",
    "OPTION_BOOLEAN",
    "OPTION_NUMBER",
    "extract_command_options",
    "bind_interaction_options",
    "missing_required_parameters",
]
