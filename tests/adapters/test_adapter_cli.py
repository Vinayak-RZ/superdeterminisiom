from __future__ import annotations

import json
from pathlib import Path

import pytest

from superdeterminism.adapters import extra_installed
from superdeterminism.cli import main


def _one_trace(tmp_path: Path) -> Path:
    payload = {
        "traces": [
            {
                "spans": [
                    {
                        "name": "chat",
                        "attributes": {"gen_ai.operation.name": "chat"},
                        "output": {"intent": "other"},
                    }
                ]
            }
        ]
    }
    path = tmp_path / "t.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_unknown_adapter_exits_2(tmp_path: Path, capsys) -> None:
    path = _one_trace(tmp_path)
    assert main(["recommend", str(path), "--adapter", "nope"]) == 2
    assert "unknown adapter" in capsys.readouterr().err


def test_langgraph_without_extra_exits_2(tmp_path: Path, capsys) -> None:
    if extra_installed("langgraph"):
        pytest.skip("langgraph extra is installed")
    path = _one_trace(tmp_path)
    assert main(["recommend", str(path), "--adapter", "langgraph"]) == 2
    assert "pip install" in capsys.readouterr().err


def test_omitted_adapter_is_p0_path(tmp_path: Path, capsys) -> None:
    path = _one_trace(tmp_path)
    assert main(["recommend", str(path), "--n-min", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommendations"][0]["node_kind"] == "llm_reasoner"
