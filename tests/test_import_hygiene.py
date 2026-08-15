from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "superdeterminism"
ALLOWED = SRC / "adapters" / "langgraph.py"
_IMPORT = re.compile(
    r"^\s*(?:import\s+(?:langchain|langgraph)|from\s+(?:langchain|langgraph)\b)",
    re.M,
)


def test_no_langchain_import_outside_langgraph_adapter() -> None:
    for path in SRC.rglob("*.py"):
        if path == ALLOWED:
            continue
        text = path.read_text(encoding="utf-8")
        assert _IMPORT.search(text) is None, path


def test_no_create_react_agent_in_src() -> None:
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "create_react_agent" not in text, path
