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
    assert payload["recommendations"][0]["node_id"] == "classify"


def test_cli_bad_input(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    assert main(["recommend", str(path)]) == 2
