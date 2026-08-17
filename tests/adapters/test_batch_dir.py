from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main


def _write_trace(path: Path, node: str) -> None:
    path.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "attributes": {
                                    "gen_ai.operation.name": "chat",
                                    "langgraph_node": node,
                                },
                                "output": {"intent": node},
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_traces_dir_one_json_report(tmp_path: Path, capsys) -> None:
    _write_trace(tmp_path / "a.json", "classify")
    _write_trace(tmp_path / "b.json", "summarize")
    assert main(["recommend", "--traces-dir", str(tmp_path), "--n-min", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    ids = {row["node_id"] for row in payload["recommendations"]}
    assert ids == {"classify", "summarize"}
    assert payload["disclaimer"].startswith("simulation")


def test_traces_dir_missing_exits_2(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main(["recommend", "--traces-dir", str(empty)]) == 2
