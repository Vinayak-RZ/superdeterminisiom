"""Lazy adapter registry. Framework modules are imported only on resolve()."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from superdeterminism.models import Trace

# ponytail: name → module path; never import adapter modules at package load
_MODULES = {
    "langgraph": "superdeterminism.adapters.langgraph",
    "custom": "examples.custom_adapter",
}
_EXTRAS = {
    "langgraph": ("langgraph", "langchain"),
}


class AdapterError(ValueError):
    """Unknown adapter or missing optional extra."""


@runtime_checkable
class Adapter(Protocol):
    """Second adapter exists (P2). load returns P0 traces only."""

    name: str

    def load(self, path_or_bytes: Path | str | bytes) -> list[Trace]: ...


def extra_installed(name: str) -> bool:
    pkgs = _EXTRAS.get(name)
    if pkgs is None:
        return True
    return all(importlib.util.find_spec(pkg) is not None for pkg in pkgs)


def resolve(name: str) -> Callable[..., Any]:
    if name not in _MODULES:
        raise AdapterError(f"unknown adapter: {name}")
    if name in _EXTRAS and not extra_installed(name):
        raise AdapterError(
            f"adapter {name} requires: pip install 'superdeterminism[{name}]'"
        )
    target = _MODULES[name]
    if target.startswith("examples."):
        root = str(Path(__file__).resolve().parents[3])
        if root not in sys.path:
            sys.path.insert(0, root)
    mod = importlib.import_module(target)
    load = getattr(mod, "load", None)
    if load is None:
        raise AdapterError(f"adapter {name} has no load()")
    return load
