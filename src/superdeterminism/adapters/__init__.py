"""Lazy adapter registry. Framework modules are imported only on resolve()."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from typing import Any

# ponytail: name → module path; never import langgraph.py at package load
_MODULES = {
    "langgraph": "superdeterminism.adapters.langgraph",
}
_EXTRAS = {
    "langgraph": ("langgraph", "langchain"),
}


class AdapterError(ValueError):
    """Unknown adapter or missing optional extra."""


def extra_installed(name: str) -> bool:
    pkgs = _EXTRAS.get(name)
    if not pkgs:
        return False
    return all(importlib.util.find_spec(pkg) is not None for pkg in pkgs)


def resolve(name: str) -> Callable[..., Any]:
    if name not in _MODULES:
        raise AdapterError(f"unknown adapter: {name}")
    if not extra_installed(name):
        raise AdapterError(
            f"adapter {name} requires: pip install 'superdeterminism[{name}]'"
        )
    mod = importlib.import_module(_MODULES[name])
    load = getattr(mod, "load", None)
    if load is None:
        raise AdapterError(f"adapter {name} has no load()")
    return load
