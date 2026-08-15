from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main


def test_cli_json_stdout(tmp_path: Path, capsys) -> None:
    traces = {
        "traces": [
            {
                "spans": [
                    {
                        "name": "chat",
                        "attributes": {
                            "gen_ai.operation.name": "chat",
                            "langgraph_node": "classify",
                        },
                        "output": {"intent": "other"},
                    }
                ]
            }
        ]
    }
    path = tmp_path / "t.json"
    path.write_text(json.dumps(traces), encoding="utf-8")
    assert main(["recommend", str(path), "--n-min", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["disclaimer"].startswith("simulation")
    assert payload["canary"]
    assert all(isinstance(item, str) and item for item in payload["canary"])
    assert "orchestrator" in payload
    assert payload["orchestrator"]["action"]
    assert payload["recommendations"][0]["node_id"] == "classify"
    assert "from_kind" in payload["recommendations"][0]
    assert "to_kind" in payload["recommendations"][0]
    assert payload["simulation"]["level"] == "l0_tape_splice"
    assert payload["simulation"]["census"]["n_traces"] == 1


def test_cli_markdown_includes_canary(tmp_path: Path, capsys) -> None:
    traces = {
        "traces": [
            {
                "spans": [
                    {
                        "name": "chat",
                        "attributes": {
                            "gen_ai.operation.name": "chat",
                            "langgraph_node": "classify",
                        },
                        "output": {"intent": "other"},
                    }
                ]
            }
        ]
    }
    path = tmp_path / "t.json"
    path.write_text(json.dumps(traces), encoding="utf-8")
    assert main(["recommend", str(path), "--n-min", "1", "--stdout", "md"]) == 0
    out = capsys.readouterr().out
    assert "## Canary checklist" in out
    assert "Not a deploy button" in out
    assert "Path census" in out


def test_cli_bad_input(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    assert main(["recommend", str(path)]) == 2
