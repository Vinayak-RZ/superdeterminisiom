from __future__ import annotations

import sys

import pytest

from superdeterminism.adapters import AdapterError, extra_installed, resolve


def test_adapters_package_does_not_import_langgraph() -> None:
    assert "superdeterminism.adapters.langgraph" not in sys.modules


def test_resolve_unknown_adapter() -> None:
    with pytest.raises(AdapterError, match="unknown adapter"):
        resolve("nope")


def test_resolve_langgraph_without_extra() -> None:
    if extra_installed("langgraph"):
        pytest.skip("langgraph extra is installed")
    with pytest.raises(AdapterError, match="pip install"):
        resolve("langgraph")
