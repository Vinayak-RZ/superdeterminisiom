from __future__ import annotations

from pathlib import Path

import superdeterminism.adapters as adapters_pkg
import pytest

from superdeterminism.adapters import AdapterError, extra_installed, resolve


def test_registry_does_not_eager_import_langgraph() -> None:
    text = Path(adapters_pkg.__file__).read_text(encoding="utf-8")
    assert "from .langgraph" not in text
    assert "from . import langgraph" not in text
    assert "importlib.import_module" in text


def test_resolve_unknown_adapter() -> None:
    with pytest.raises(AdapterError, match="unknown adapter"):
        resolve("nope")


def test_resolve_langgraph_without_extra() -> None:
    if extra_installed("langgraph"):
        pytest.skip("langgraph extra is installed")
    with pytest.raises(AdapterError, match="pip install"):
        resolve("langgraph")
