from __future__ import annotations

import json
from pathlib import Path

from examples.custom_adapter import NAME, load
from superdeterminism.cli import main
from superdeterminism.pipeline import recommend_traces


def test_custom_example_shape_and_recommend(tmp_path: Path) -> None:
    assert NAME == "custom"
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
    traces = load(path)
    recs = recommend_traces(traces, n_min=1)
    assert recs
    assert recs[0].node_kind.value == "llm_reasoner"


def test_cli_adapter_custom(tmp_path: Path, capsys) -> None:
    path = tmp_path / "t.json"
    path.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "attributes": {"gen_ai.operation.name": "chat"},
                                "output": {"ok": True},
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["recommend", str(path), "--adapter", "custom", "--n-min", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["disclaimer"].startswith("simulation")
    assert payload["recommendations"]
